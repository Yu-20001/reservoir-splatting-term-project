from pathlib import Path
import statistics

m.script("scripts/ReservoirSplatting.py")
m.resizeFrameBuffer(960, 540)
m.loadScene("data/scenes/reservoir_splatting_dynamic_cornell_box.pyscene")
m.scene.camera.shutterSpeed = 0.05

graph = m.getGraph("ReservoirSplatting")
output_dir = Path("phase3-results/frame-dumper-multi-splatting")
output_dir.mkdir(parents=True, exist_ok=True)
timing_path = Path("phase3-results/frame-dumper-multi-splatting.csv")
for path in output_dir.glob("frame.*.pam"):
    path.unlink()

graph.updatePass("ReservoirSplatting", {
    "samplesPerPixel": 1,
    "enableTemporalResampling": True,
    "enableSpatialResampling": True,
    "temporalReuse": "MultiScatter",
    "numTimePartitions": 2,
    "scatterBackupMISOption": "Balance",
})
graph.updatePass("FrameDumper", {
    "outputDir": str(output_dir),
    "outputBase": "frame",
    "frameOffset": 0,
})

reservoir_splatting = graph.getPass("ReservoirSplatting")
frame_dumper = graph.getPass("FrameDumper")
reservoir_splatting.resetDynamicObject()
frame_dumper.usePng = False

for _ in range(16):
    m.renderFrame()

m.timingCapture.captureFrameTime(timing_path)
if not frame_dumper.startCapture():
    raise RuntimeError("FrameDumper output directory is unavailable.")
if not reservoir_splatting.spawnDynamicObject():
    raise RuntimeError("Dynamic sphere node is unavailable.")

while reservoir_splatting.dynamicObjectActive:
    m.renderFrame()

frame_dumper.stopCapture()
m.timingCapture.captureFrameTime("")

with timing_path.open() as f:
    frame_times = [float(line) for line in f if line.strip()]

mean_seconds = statistics.fmean(frame_times)
frame_count = len(list(output_dir.glob("frame.*.pam")))
print(f"multi-splatting-frame-dumper: frames={len(frame_times)} output_frames={frame_count} mean_ms={mean_seconds * 1000.0:.3f} mean_fps={1.0 / mean_seconds:.2f}")

exit()
