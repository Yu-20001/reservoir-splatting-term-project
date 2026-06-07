#!/usr/bin/env python3
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "disocclusion-results"
THRESHOLDS = ["0.01", "0.02", "0.04"]
METRICS = {"nrmse", "log_luma_mae"}


def read_summary(path):
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


rows = []
for threshold in THRESHOLDS:
    analysis_dir = RESULT_ROOT / f"analysis-threshold-{threshold}"
    for row in read_summary(analysis_dir / "summary.csv"):
        if row["metric"] in METRICS:
            rows.append(
                (
                    threshold,
                    row["mode"],
                    row["metric"],
                    row["mean"],
                    row["ci95_low"],
                    row["ci95_high"],
                )
            )

output_path = RESULT_ROOT / "analysis" / "threshold-sensitivity.csv"
with output_path.open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["position_threshold", "mode", "metric", "mean", "ci95_low", "ci95_high"])
    writer.writerows(rows)

print(f"Wrote {output_path}")
