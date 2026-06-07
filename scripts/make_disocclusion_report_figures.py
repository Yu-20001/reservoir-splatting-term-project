#!/usr/bin/env python3
import csv
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import OpenImageIO as oiio


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "disocclusion-results"
CAPTURE_DIR = RESULT_ROOT / "captures"
ANALYSIS_DIR = RESULT_ROOT / "analysis"
FIGURE_DIR = RESULT_ROOT / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

MODES = ["gather-robust", "scatter-only", "scatter-backup"]
LABELS = {
    "gather-robust": "GatherOnly + Robust",
    "scatter-only": "ScatterOnly",
    "scatter-backup": "ScatterBackup",
}
COLORS = {
    "gather-robust": "#4C78A8",
    "scatter-only": "#F58518",
    "scatter-backup": "#54A24B",
}


def read_csv(path):
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


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


def write_png(path, image):
    image = np.clip(image, 0.0, 1.0)
    height, width, channels = image.shape
    output = oiio.ImageOutput.create(str(path))
    output.open(str(path), oiio.ImageSpec(width, height, channels, oiio.UINT8))
    output.write_image((image * 255.0 + 0.5).astype(np.uint8))
    output.close()


def display_map(image):
    rgb = np.maximum(image[..., :3], 0.0)
    rgb = rgb / (1.0 + rgb)
    return np.power(rgb, 1.0 / 2.2)


def svg_text(x, y, text, size=18, anchor="middle", weight="normal"):
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
        f'font-family="DejaVu Sans, sans-serif" font-size="{size}" font-weight="{weight}">{text}</text>'
    )


def save_svg_png(name, width, height, elements):
    svg_path = FIGURE_DIR / f"{name}.svg"
    png_path = FIGURE_DIR / f"{name}.png"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        '<rect width="100%" height="100%" fill="white"/>'
        + "".join(elements)
        + "</svg>"
    )
    svg_path.write_text(svg)
    subprocess.run(["magick", str(svg_path), str(png_path)], check=True)


def make_summary_chart(summary, floor):
    rows = {row["mode"]: row for row in summary if row["metric"] == "log_luma_mae"}
    floor_mean = np.mean([float(row["log_luma_mae"]) for row in floor])
    width, height = 1000, 620
    left, top, chart_width, chart_height = 110, 85, 820, 410
    maximum = 0.11
    elements = [svg_text(width / 2, 42, "Error on Newly Revealed Pixels", 27, weight="bold")]

    for tick in np.linspace(0, maximum, 6):
        y = top + chart_height * (1.0 - tick / maximum)
        elements.append(f'<line x1="{left}" y1="{y}" x2="{left + chart_width}" y2="{y}" stroke="#dddddd"/>')
        elements.append(svg_text(left - 15, y + 6, f"{tick:.2f}", 16, "end"))

    bar_width = 150
    for index, mode in enumerate(MODES):
        row = rows[mode]
        mean = float(row["mean"])
        low = float(row["ci95_low"])
        high = float(row["ci95_high"])
        center = left + chart_width * (index + 0.5) / len(MODES)
        y = top + chart_height * (1.0 - mean / maximum)
        bottom = top + chart_height
        error_top = top + chart_height * (1.0 - high / maximum)
        error_bottom = top + chart_height * (1.0 - low / maximum)
        elements.append(
            f'<rect x="{center - bar_width / 2}" y="{y}" width="{bar_width}" height="{bottom - y}" fill="{COLORS[mode]}"/>'
        )
        elements.append(f'<line x1="{center}" y1="{error_top}" x2="{center}" y2="{error_bottom}" stroke="black" stroke-width="3"/>')
        elements.append(f'<line x1="{center - 12}" y1="{error_top}" x2="{center + 12}" y2="{error_top}" stroke="black" stroke-width="3"/>')
        elements.append(f'<line x1="{center - 12}" y1="{error_bottom}" x2="{center + 12}" y2="{error_bottom}" stroke="black" stroke-width="3"/>')
        elements.append(svg_text(center, bottom + 32, LABELS[mode], 17))
        elements.append(svg_text(center, y - 12, f"{mean:.4f}", 16))

    floor_y = top + chart_height * (1.0 - floor_mean / maximum)
    elements.append(f'<line x1="{left}" y1="{floor_y}" x2="{left + chart_width}" y2="{floor_y}" stroke="black" stroke-width="2" stroke-dasharray="8,6"/>')
    elements.append(svg_text(left + chart_width - 5, floor_y - 8, f"Reference noise floor: {floor_mean:.4f}", 15, "end"))
    label_y = top + chart_height / 2
    elements.append(
        f'<text x="30" y="{label_y}" text-anchor="middle" transform="rotate(-90 30 {label_y})" '
        'font-family="DejaVu Sans, sans-serif" font-size="18" font-weight="bold">Masked log-luminance MAE</text>'
    )
    save_svg_png("disocclusion-error-summary", width, height, elements)


def make_time_chart(per_frame):
    width, height = 1000, 620
    left, top, chart_width, chart_height = 110, 75, 820, 430
    maximum = 0.14
    elements = [svg_text(width / 2, 38, "Disocclusion Error Along the Camera Path", 27, weight="bold")]

    for tick in np.linspace(0, maximum, 8):
        y = top + chart_height * (1.0 - tick / maximum)
        elements.append(f'<line x1="{left}" y1="{y}" x2="{left + chart_width}" y2="{y}" stroke="#dddddd"/>')
        elements.append(svg_text(left - 15, y + 6, f"{tick:.2f}", 16, "end"))

    frames = sorted({int(row["frame"]) for row in per_frame})
    for mode_index, mode in enumerate(MODES):
        points = []
        for frame in frames:
            values = [
                float(row["log_luma_mae"])
                for row in per_frame
                if row["mode"] == mode and int(row["frame"]) == frame
            ]
            mean = float(np.mean(values))
            x = left + chart_width * (frame - frames[0]) / (frames[-1] - frames[0])
            y = top + chart_height * (1.0 - mean / maximum)
            points.append((x, y))
        point_text = " ".join(f"{x},{y}" for x, y in points)
        elements.append(f'<polyline points="{point_text}" fill="none" stroke="{COLORS[mode]}" stroke-width="4"/>')
        for x, y in points:
            elements.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{COLORS[mode]}"/>')
        legend_x = left + mode_index * 265
        elements.append(f'<line x1="{legend_x}" y1="555" x2="{legend_x + 35}" y2="555" stroke="{COLORS[mode]}" stroke-width="5"/>')
        elements.append(svg_text(legend_x + 45, 561, LABELS[mode], 16, "start"))

    for frame in frames:
        x = left + chart_width * (frame - frames[0]) / (frames[-1] - frames[0])
        elements.append(svg_text(x, top + chart_height + 28, str(frame), 15))
    elements.append(svg_text(width / 2, height - 22, "Camera-path frame", 18, weight="bold"))
    label_y = top + chart_height / 2
    elements.append(
        f'<text x="30" y="{label_y}" text-anchor="middle" transform="rotate(-90 30 {label_y})" '
        'font-family="DejaVu Sans, sans-serif" font-size="18" font-weight="bold">Masked log-luminance MAE</text>'
    )
    save_svg_png("disocclusion-error-over-time", width, height, elements)


def make_representative_figure():
    frame = 44
    reference_a = read_image(find_capture(f"reference-seed-50021-frame-{frame:02d}", "AccumulatePass.output"))
    reference_b = read_image(find_capture(f"reference-seed-90001-frame-{frame:02d}", "AccumulatePass.output"))
    reference = 0.5 * (reference_a + reference_b)
    mask = read_image(ANALYSIS_DIR / f"disocclusion-mask-frame-{frame:02d}.exr")[..., :3]
    images = [("Reference", reference)]
    for mode in MODES:
        images.append(
            (
                LABELS[mode],
                read_image(find_capture(f"test-{mode}-seed-101-frame-{frame:02d}", "AccumulatePass.output")),
            )
        )
    images.append(("Disocclusion Mask", mask))

    with tempfile.TemporaryDirectory() as temp_dir:
        labeled = []
        for index, (label, image) in enumerate(images):
            image_path = Path(temp_dir) / f"{index}.png"
            labeled_path = Path(temp_dir) / f"{index}-labeled.png"
            write_png(image_path, display_map(image) if label != "Disocclusion Mask" else image)
            subprocess.run(
                [
                    "magick",
                    str(image_path),
                    "-resize",
                    "576x324",
                    "-gravity",
                    "north",
                    "-background",
                    "white",
                    "-splice",
                    "0x56",
                    "-font",
                    "DejaVu-Sans",
                    "-pointsize",
                    "24",
                    "-fill",
                    "black",
                    "-annotate",
                    "+0+14",
                    label,
                    str(labeled_path),
                ],
                check=True,
            )
            labeled.append(str(labeled_path))
        subprocess.run(
            [
                "magick",
                "montage",
                *labeled,
                "-tile",
                "3x2",
                "-geometry",
                "+12+12",
                "-background",
                "white",
                str(FIGURE_DIR / "disocclusion-representative-frame-44.png"),
            ],
            check=True,
        )


summary = read_csv(ANALYSIS_DIR / "summary.csv")
floor = read_csv(ANALYSIS_DIR / "reference-noise-floor.csv")
per_frame = read_csv(ANALYSIS_DIR / "per-run-frame-metrics.csv")
make_summary_chart(summary, floor)
make_time_chart(per_frame)
make_representative_figure()
print(f"Wrote disocclusion report figures to {FIGURE_DIR}")
