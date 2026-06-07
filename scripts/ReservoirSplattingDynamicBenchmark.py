from pathlib import Path
import csv
import statistics

m.script("scripts/ReservoirSplatting.py")
m.resizeFrameBuffer(960, 540)
m.loadScene("data/scenes/reservoir_splatting_dynamic_cornell_box.pyscene")
m.scene.camera.shutterSpeed = 0.05

graph = m.getGraph("ReservoirSplatting")
output_dir = Path("benchmark-results")
output_dir.mkdir(exist_ok=True)

modes = [
    ("gather-robust", {"temporalReuse": "GatherOnly", "gatherOption": "Robust"}),
    ("scatter-backup", {"temporalReuse": "ScatterBackup", "gatherOption": "Robust"}),
    ("multi-splatting", {"temporalReuse": "MultiScatter"}),
]

common = {
    "samplesPerPixel": 1,
    "enableTemporalResampling": True,
    "enableSpatialResampling": True,
    "numTimePartitions": 2,
    "scatterBackupMISOption": "Balance",
}

results = []
for name, mode in modes:
    graph.updatePass("ReservoirSplatting", {**common, **mode})
    reservoir_splatting = graph.getPass("ReservoirSplatting")
    reservoir_splatting.resetDynamicObject()

    for _ in range(16):
        m.renderFrame()

    output_path = output_dir / f"dynamic-object-{name}.csv"
    m.timingCapture.captureFrameTime(output_path)
    if not reservoir_splatting.spawnDynamicObject():
        raise RuntimeError("Dynamic sphere node is unavailable.")

    for _ in range(180):
        m.renderFrame()
        if not reservoir_splatting.dynamicObjectActive:
            break

    m.timingCapture.captureFrameTime("")

    with output_path.open() as f:
        frame_times = [float(line) for line in f if line.strip()]

    mean_seconds = statistics.fmean(frame_times)
    results.append((name, len(frame_times), mean_seconds * 1000.0, 1.0 / mean_seconds))

summary_path = output_dir / "dynamic-object-summary.csv"
with summary_path.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["mode", "frames", "mean_ms", "mean_fps"])
    writer.writerows(results)

for name, frames, mean_ms, mean_fps in results:
    print(f"{name}: frames={frames} mean_ms={mean_ms:.3f} mean_fps={mean_fps:.2f}")

exit()
