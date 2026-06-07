#!/usr/bin/env python3
import csv
import math
import os
from pathlib import Path

import OpenImageIO as oiio
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = Path(os.environ.get("DISOCCLUSION_OUTPUT_ROOT", ROOT / "disocclusion-results"))
CAPTURE_DIR = RESULT_ROOT / "captures"
OUTPUT_DIR = RESULT_ROOT / os.environ.get("DISOCCLUSION_ANALYSIS_NAME", "analysis")
TARGET_FRAMES = [
    int(frame)
    for frame in os.environ.get("DISOCCLUSION_TARGET_FRAMES", "8,17,26,35,44,53,62,71,80,89").split(",")
]
MODES = ["gather-robust", "scatter-only", "scatter-backup"]
RUN_SEEDS = [int(seed) for seed in os.environ.get("DISOCCLUSION_RUN_SEEDS", "101,1009,2027,4093,8089").split(",")]
REFERENCE_SEEDS = [int(seed) for seed in os.environ.get("DISOCCLUSION_REFERENCE_SEEDS", "50021,90001").split(",")]
POSITION_THRESHOLD = float(os.environ.get("DISOCCLUSION_POSITION_THRESHOLD", "0.02"))


def find_capture(prefix, output):
    matches = sorted(CAPTURE_DIR.glob(f"{prefix}.{output}.*.exr"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one capture for {prefix}.{output}, found {len(matches)}")
    return matches[0]


def read_image(path):
    image = oiio.ImageBuf(str(path))
    spec = image.spec()
    pixels = image.get_pixels(oiio.FLOAT)
    return np.asarray(pixels, dtype=np.float32).reshape(spec.height, spec.width, spec.nchannels)


def write_image(path, pixels):
    height, width, channels = pixels.shape
    spec = oiio.ImageSpec(width, height, channels, oiio.FLOAT)
    output = oiio.ImageOutput.create(str(path))
    output.open(str(path), spec)
    output.write_image(pixels.astype(np.float32))
    output.close()


def bilinear_sample(image, x, y):
    height, width = image.shape[:2]
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, width - 1)
    y1 = np.clip(y0 + 1, 0, height - 1)
    x0 = np.clip(x0, 0, width - 1)
    y0 = np.clip(y0, 0, height - 1)
    tx = (x - x0)[..., None]
    ty = (y - y0)[..., None]
    top = image[y0, x0] * (1.0 - tx) + image[y0, x1] * tx
    bottom = image[y1, x0] * (1.0 - tx) + image[y1, x1] * tx
    return top * (1.0 - ty) + bottom * ty


def dilate(mask, radius=1):
    result = mask.copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            shifted = np.roll(mask, (dy, dx), axis=(0, 1))
            if dy < 0:
                shifted[dy:] = False
            elif dy > 0:
                shifted[:dy] = False
            if dx < 0:
                shifted[:, dx:] = False
            elif dx > 0:
                shifted[:, :dx] = False
            result |= shifted
    return result


def build_disocclusion_mask(frame):
    current_prefix = f"geometry-frame-{frame:02d}"
    previous_prefix = f"geometry-frame-{frame - 1:02d}"
    current_pos = read_image(find_capture(current_prefix, "VBufferRT.posW"))[..., :3]
    previous_pos = read_image(find_capture(previous_prefix, "VBufferRT.posW"))[..., :3]
    motion = read_image(find_capture(current_prefix, "VBufferRT.mvec"))[..., :2]
    current_valid = read_image(find_capture(current_prefix, "VBufferRT.mask"))[..., 0] > 0.5
    previous_valid = read_image(find_capture(previous_prefix, "VBufferRT.mask"))[..., 0] > 0.5

    height, width = current_valid.shape
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    previous_x = xx + motion[..., 0] * width
    previous_y = yy + motion[..., 1] * height
    in_bounds = (
        (previous_x >= 0.0)
        & (previous_x <= width - 1)
        & (previous_y >= 0.0)
        & (previous_y <= height - 1)
    )
    sampled_pos = bilinear_sample(previous_pos, previous_x, previous_y)
    sampled_valid = bilinear_sample(previous_valid[..., None].astype(np.float32), previous_x, previous_y)[..., 0] > 0.99
    position_error = np.linalg.norm(current_pos - sampled_pos, axis=2)
    mask = current_valid & (~in_bounds | ~sampled_valid | (position_error > POSITION_THRESHOLD))
    return dilate(mask, radius=1)


def luminance(rgb):
    return np.maximum(rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722, 0.0)


def metrics(test, reference, mask):
    test = test[..., :3]
    reference = reference[..., :3]
    if not np.all(np.isfinite(reference)):
        raise RuntimeError("Reference image contains non-finite pixels")
    finite = np.all(np.isfinite(test), axis=2)
    masked_nonfinite_rate = float(np.mean(~finite[mask]))
    full_nonfinite_rate = float(np.mean(~finite))
    test = np.where(np.isfinite(test), test, 0.0)
    diff = test - reference
    selected = diff[mask]
    selected_reference = reference[mask]
    if selected.size == 0:
        raise RuntimeError("Disocclusion mask is empty")
    rmse = math.sqrt(float(np.mean(selected * selected)))
    reference_rms = math.sqrt(float(np.mean(selected_reference * selected_reference)))
    nrmse = rmse / max(reference_rms, 1e-8)
    test_log_luma = np.log1p(luminance(test)[mask])
    reference_log_luma = np.log1p(luminance(reference)[mask])
    log_luma_mae = float(np.mean(np.abs(test_log_luma - reference_log_luma)))
    luminance_bias = float(np.mean(luminance(test)[mask] - luminance(reference)[mask]))
    return nrmse, log_luma_mae, luminance_bias, masked_nonfinite_rate, full_nonfinite_rate


def confidence_interval(values):
    values = np.asarray(values, dtype=np.float64)
    mean = float(np.mean(values))
    if len(values) == 1:
        return mean, mean, mean
    half_width = 1.96 * float(np.std(values, ddof=1)) / math.sqrt(len(values))
    return mean, mean - half_width, mean + half_width


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    reference_floor_rows = []

    for frame in TARGET_FRAMES:
        mask = build_disocclusion_mask(frame)
        mask_rgb = np.repeat(mask[..., None].astype(np.float32), 3, axis=2)
        write_image(OUTPUT_DIR / f"disocclusion-mask-frame-{frame:02d}.exr", mask_rgb)

        references = [
            read_image(find_capture(f"reference-seed-{seed}-frame-{frame:02d}", "AccumulatePass.output"))
            for seed in REFERENCE_SEEDS
        ]
        reference = 0.5 * (references[0] + references[1])
        floor = metrics(references[0], references[1], mask)
        reference_floor_rows.append((frame, int(mask.sum()), *floor))

        for mode in MODES:
            for seed in RUN_SEEDS:
                test = read_image(
                    find_capture(f"test-{mode}-seed-{seed}-frame-{frame:02d}", "AccumulatePass.output")
                )
                rows.append((mode, seed, frame, int(mask.sum()), *metrics(test, reference, mask)))

    with (OUTPUT_DIR / "per-run-frame-metrics.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "mode",
                "seed",
                "frame",
                "mask_pixels",
                "nrmse",
                "log_luma_mae",
                "luminance_bias",
                "masked_nonfinite_rate",
                "full_nonfinite_rate",
            ]
        )
        writer.writerows(rows)

    with (OUTPUT_DIR / "reference-noise-floor.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "frame",
                "mask_pixels",
                "nrmse",
                "log_luma_mae",
                "luminance_bias",
                "masked_nonfinite_rate",
                "full_nonfinite_rate",
            ]
        )
        writer.writerows(reference_floor_rows)

    summary_rows = []
    metric_columns = [
        (4, "nrmse"),
        (5, "log_luma_mae"),
        (6, "luminance_bias"),
        (7, "masked_nonfinite_rate"),
        (8, "full_nonfinite_rate"),
    ]
    seed_aggregates = {}
    for mode in MODES:
        for seed in RUN_SEEDS:
            seed_rows = [row for row in rows if row[0] == mode and row[1] == seed]
            seed_aggregates[(mode, seed)] = {
                metric_name: float(np.mean([row[metric_index] for row in seed_rows]))
                for metric_index, metric_name in metric_columns
            }
        for _, metric_name in metric_columns:
            values = [seed_aggregates[(mode, seed)][metric_name] for seed in RUN_SEEDS]
            mean, ci_low, ci_high = confidence_interval(values)
            summary_rows.append((mode, metric_name, len(values), mean, ci_low, ci_high))

    with (OUTPUT_DIR / "summary.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["mode", "metric", "samples", "mean", "ci95_low", "ci95_high"])
        writer.writerows(summary_rows)

    comparison_rows = []
    for left_index, left in enumerate(MODES):
        for right in MODES[left_index + 1 :]:
            for metric_name in ["nrmse", "log_luma_mae", "luminance_bias"]:
                differences = [
                    seed_aggregates[(left, seed)][metric_name] - seed_aggregates[(right, seed)][metric_name]
                    for seed in RUN_SEEDS
                ]
                mean, ci_low, ci_high = confidence_interval(differences)
                comparison_rows.append((left, right, metric_name, len(differences), mean, ci_low, ci_high))

    with (OUTPUT_DIR / "paired-comparisons.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["left", "right", "metric", "paired_seeds", "left_minus_right_mean", "ci95_low", "ci95_high"])
        writer.writerows(comparison_rows)

    print(f"Wrote disocclusion analysis to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
