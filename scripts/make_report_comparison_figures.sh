#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
input_dir="$repo_root/phase3-results/representative-frames"
output_dir="$repo_root/report-assets/figures"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

mkdir -p "$output_dir"

declare -a modes=(
    "no-temporal-reuse|No Temporal Reuse|dynamic-object-no-temporal-reuse.FrameDumper.dst.121.png"
    "gather-robust|GatherOnly + Robust|dynamic-object-gather-robust.FrameDumper.dst.242.png"
    "scatter-only|ScatterOnly|dynamic-object-scatter-only.FrameDumper.dst.363.png"
    "scatter-backup|ScatterBackup|dynamic-object-scatter-backup.FrameDumper.dst.484.png"
    "multi-splatting|MultiSplatting|dynamic-object-multi-splatting.FrameDumper.dst.605.png"
)

for entry in "${modes[@]}"; do
    IFS='|' read -r slug label filename <<< "$entry"
    source_image="$input_dir/$filename"

    # Remove the viewport letterboxing while preserving identical scene coordinates.
    magick "$source_image" -crop 472x472+244+38 +repage \
        -resize 600x600 \
        -bordercolor white -border 8 \
        -gravity north -background white -splice 0x72 \
        -font DejaVu-Sans -pointsize 30 -fill black \
        -annotate +0+20 "$label" \
        "$work_dir/full-$slug.png"

    # Region A: moving sphere and the disocclusion boundary above the tall box.
    magick "$source_image" -crop 220x210+370+125 +repage \
        -filter point -resize 660x630 \
        -bordercolor white -border 8 \
        -gravity north -background white -splice 0x72 \
        -font DejaVu-Sans -pointsize 30 -fill black \
        -annotate +0+20 "$label" \
        "$work_dir/sphere-$slug.png"

done

magick montage \
    "$work_dir/full-no-temporal-reuse.png" \
    "$work_dir/full-gather-robust.png" \
    "$work_dir/full-scatter-only.png" \
    "$work_dir/full-scatter-backup.png" \
    "$work_dir/full-multi-splatting.png" \
    -tile 3x2 -geometry +20+20 -background white \
    "$output_dir/dynamic-object-five-mode-comparison.png"

magick montage \
    "$work_dir/sphere-no-temporal-reuse.png" \
    "$work_dir/sphere-gather-robust.png" \
    "$work_dir/sphere-scatter-only.png" \
    "$work_dir/sphere-scatter-backup.png" \
    "$work_dir/sphere-multi-splatting.png" \
    -tile 5x1 -geometry +12+12 -background white \
    "$output_dir/dynamic-object-detail-crops.png"

printf 'Wrote report figures to %s\n' "$output_dir"
