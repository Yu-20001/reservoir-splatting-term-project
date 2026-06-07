from pathlib import Path
import csv

m.script("scripts/ReservoirSplatting.py")
m.resizeFrameBuffer(960, 540)
m.loadScene("data/scenes/reservoir_splatting_dynamic_cornell_box.pyscene")
m.scene.camera.shutterSpeed = 0.05

graph = m.getGraph("ReservoirSplatting")
output_dir = Path("phase3-results")
frame_dir = output_dir / "representative-frames"
frame_dir.mkdir(parents=True, exist_ok=True)

m.frameCapture.outputDir = frame_dir.resolve()
m.frameCapture.captureAllOutputs = False

modes = [
    ("no-temporal-reuse", {"enableTemporalResampling": False}),
    ("gather-robust", {"temporalReuse": "GatherOnly", "gatherOption": "Robust"}),
    ("scatter-only", {"temporalReuse": "ScatterOnly"}),
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

gpu_event = "/onFrameRender/gpu_time"
snapshot_frame = 32
results = []

for name, mode in modes:
    graph.updatePass("ReservoirSplatting", {**common, **mode})
    reservoir_splatting = graph.getPass("ReservoirSplatting")
    reservoir_splatting.resetDynamicObject()

    for _ in range(16):
        m.renderFrame()

    m.profiler.enabled = True
    m.profiler.start_capture()
    if not reservoir_splatting.spawnDynamicObject():
        raise RuntimeError("Dynamic sphere node is unavailable.")

    while reservoir_splatting.dynamicObjectActive:
        m.renderFrame()

    capture = m.profiler.end_capture()
    m.profiler.enabled = False
    stats = capture["events"][gpu_event]["stats"]
    results.append((name, capture["frame_count"], stats["mean"], stats["std_dev"], stats["min"], stats["max"]))

    reservoir_splatting.resetDynamicObject()
    for _ in range(4):
        m.renderFrame()
    reservoir_splatting.spawnDynamicObject()
    for _ in range(snapshot_frame):
        m.renderFrame()
    m.frameCapture.baseFilename = f"dynamic-object-{name}"
    m.frameCapture.capture()

summary_path = output_dir / "dynamic-object-gpu-summary.csv"
with summary_path.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["mode", "frames", "gpu_mean_ms", "gpu_stddev_ms", "gpu_min_ms", "gpu_max_ms"])
    writer.writerows(results)

for name, frames, mean_ms, stddev_ms, min_ms, max_ms in results:
    print(
        f"{name}: frames={frames} gpu_mean_ms={mean_ms:.3f} gpu_stddev_ms={stddev_ms:.3f} "
        f"gpu_min_ms={min_ms:.3f} gpu_max_ms={max_ms:.3f}"
    )

exit()
