#!/usr/bin/env python3
import csv
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "phase3-results" / "dynamic-object-gpu-summary.csv"
OUTPUT_DIR = ROOT / "report-assets" / "figures"

MODE_ORDER = [
    "no-temporal-reuse",
    "gather-robust",
    "scatter-only",
    "scatter-backup",
    "multi-splatting",
]
LABELS = {
    "no-temporal-reuse": ("No Temporal", "Reuse"),
    "gather-robust": ("GatherOnly", "+ Robust"),
    "scatter-only": ("ScatterOnly", ""),
    "scatter-backup": ("ScatterBackup", ""),
    "multi-splatting": ("MultiSplatting", ""),
}
COLORS = {
    "no-temporal-reuse": "#9E9E9E",
    "gather-robust": "#4C78A8",
    "scatter-only": "#F58518",
    "scatter-backup": "#E45756",
    "multi-splatting": "#54A24B",
}


def text(x, y, value, size=20, anchor="middle", weight="normal", fill="#222222"):
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
        f'font-family="DejaVu Sans, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}">{value}</text>'
    )


with INPUT.open(newline="") as file:
    rows = {row["mode"]: row for row in csv.DictReader(file)}

missing = [mode for mode in MODE_ORDER if mode not in rows]
if missing:
    raise RuntimeError(f"Missing modes in {INPUT}: {', '.join(missing)}")

frame_counts = {int(rows[mode]["frames"]) for mode in MODE_ORDER}
if len(frame_counts) != 1:
    raise RuntimeError(f"Expected equal frame counts, found {sorted(frame_counts)}")
frame_count = frame_counts.pop()

width, height = 1200, 720
left, top = 125, 95
chart_width, chart_height = 1000, 470
maximum = 6.0
bar_width = 145
elements = [
    '<rect width="100%" height="100%" fill="white"/>',
    text(width / 2, 48, "Mean GPU Frame Time by Temporal Reuse Mode", 30, weight="bold"),
]

for tick in range(0, 7):
    y = top + chart_height * (1.0 - tick / maximum)
    stroke = "#666666" if tick == 0 else "#DDDDDD"
    elements.append(
        f'<line x1="{left}" y1="{y}" x2="{left + chart_width}" y2="{y}" '
        f'stroke="{stroke}" stroke-width="1"/>'
    )
    elements.append(text(left - 18, y + 7, str(tick), 18, anchor="end"))

for index, mode in enumerate(MODE_ORDER):
    mean = float(rows[mode]["gpu_mean_ms"])
    stddev = float(rows[mode]["gpu_stddev_ms"])
    center = left + chart_width * (index + 0.5) / len(MODE_ORDER)
    bar_top = top + chart_height * (1.0 - mean / maximum)
    bottom = top + chart_height
    elements.append(
        f'<rect x="{center - bar_width / 2}" y="{bar_top}" width="{bar_width}" '
        f'height="{bottom - bar_top}" rx="4" fill="{COLORS[mode]}"/>'
    )
    error_top = top + chart_height * (1.0 - (mean + stddev) / maximum)
    error_bottom = top + chart_height * (1.0 - (mean - stddev) / maximum)
    elements.append(
        f'<line x1="{center}" y1="{error_top}" x2="{center}" y2="{error_bottom}" '
        f'stroke="#222222" stroke-width="3"/>'
    )
    elements.append(
        f'<line x1="{center - 16}" y1="{error_top}" x2="{center + 16}" y2="{error_top}" '
        f'stroke="#222222" stroke-width="3"/>'
    )
    elements.append(
        f'<line x1="{center - 16}" y1="{error_bottom}" x2="{center + 16}" y2="{error_bottom}" '
        f'stroke="#222222" stroke-width="3"/>'
    )
    elements.append(text(center, error_top - 14, f"{mean:.3f} ms", 19, weight="bold"))
    first_line, second_line = LABELS[mode]
    elements.append(text(center, bottom + 34, first_line, 18, weight="bold"))
    if second_line:
        elements.append(text(center, bottom + 58, second_line, 18, weight="bold"))

label_y = top + chart_height / 2
elements.append(
    f'<text x="34" y="{label_y}" text-anchor="middle" '
    f'transform="rotate(-90 34 {label_y})" '
    f'font-family="DejaVu Sans, sans-serif" font-size="21" '
    f'font-weight="bold" fill="#222222">Mean GPU frame time (ms)</text>'
)
elements.append(
    text(
        width / 2,
        height - 30,
        f"Mean +/- 1 standard deviation; falling-sphere experiment, 960x540, 1 spp; n = {frame_count} frames per mode",
        17,
        fill="#555555",
    )
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
svg_path = OUTPUT_DIR / "dynamic-object-gpu-frame-time.svg"
png_path = OUTPUT_DIR / "dynamic-object-gpu-frame-time.png"
svg_path.write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">{"".join(elements)}</svg>\n'
)
subprocess.run(["magick", "-density", "180", str(svg_path), str(png_path)], check=True)
print(f"Wrote {svg_path}")
print(f"Wrote {png_path}")
