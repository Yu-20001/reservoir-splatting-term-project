#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
input_dir="$repo_root/phase3-results/arcade-camera-motion"
output_dir="$repo_root/report-assets/arcade-camera-motion"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

mkdir -p "$output_dir"

declare -a modes=(
    "gather-robust|GatherOnly + Robust"
    "scatter-backup|ScatterBackup"
    "multi-splatting|MultiSplatting"
)

selected_frame=85
frame_name="$(printf 'frame.%05d.pam' "$selected_frame")"

printf 'frame,gather_vs_scatter_mae,gather_vs_multi_mae,scatter_vs_multi_mae\n' \
    > "$output_dir/pairwise-mae.csv"

for frame in $(seq 0 89); do
    frame_file="$(printf 'frame.%05d.pam' "$frame")"
    gather="$input_dir/gather-robust/$frame_file"
    scatter="$input_dir/scatter-backup/$frame_file"
    multi="$input_dir/multi-splatting/$frame_file"

    gather_scatter="$({ compare -metric MAE "$gather" "$scatter" null: 2>&1 || true; } | sed -E 's/.*\(([^)]+)\).*/\1/')"
    gather_multi="$({ compare -metric MAE "$gather" "$multi" null: 2>&1 || true; } | sed -E 's/.*\(([^)]+)\).*/\1/')"
    scatter_multi="$({ compare -metric MAE "$scatter" "$multi" null: 2>&1 || true; } | sed -E 's/.*\(([^)]+)\).*/\1/')"

    printf '%d,%s,%s,%s\n' "$frame" "$gather_scatter" "$gather_multi" "$scatter_multi" \
        >> "$output_dir/pairwise-mae.csv"
done

for entry in "${modes[@]}"; do
    IFS='|' read -r slug label <<< "$entry"
    source_image="$input_dir/$slug/$frame_name"

    magick "$source_image" -resize 960x540 \
        -bordercolor white -border 8 \
        -gravity north -background white -splice 0x64 \
        -font DejaVu-Sans -pointsize 30 -fill black \
        -annotate +0+18 "$label" \
        "$work_dir/full-$slug.png"

    # Left edge contains the newly revealed region during the camera pan.
    magick "$source_image" -crop 300x540+0+0 +repage \
        -filter point -resize 600x1080 \
        -bordercolor white -border 8 \
        -gravity north -background white -splice 0x64 \
        -font DejaVu-Sans -pointsize 30 -fill black \
        -annotate +0+18 "$label" \
        "$work_dir/crop-$slug.png"
done

magick montage \
    "$work_dir/full-gather-robust.png" \
    "$work_dir/full-scatter-backup.png" \
    "$work_dir/full-multi-splatting.png" \
    -tile 3x1 -geometry +16+16 -background white \
    "$output_dir/arcade-camera-motion-frame-85.png"

magick montage \
    "$work_dir/crop-gather-robust.png" \
    "$work_dir/crop-scatter-backup.png" \
    "$work_dir/crop-multi-splatting.png" \
    -tile 3x1 -geometry +16+16 -background white \
    "$output_dir/arcade-camera-motion-frame-85-disocclusion-crop.png"

printf 'Wrote Arcade camera-motion assets to %s\n' "$output_dir"
