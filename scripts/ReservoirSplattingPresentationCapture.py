from pathlib import Path

m.script("scripts/ReservoirSplatting.py")
m.resizeFrameBuffer(960, 540)
m.loadScene("data/scenes/reservoir_splatting_dynamic_cornell_box.pyscene")
m.scene.camera.shutterSpeed = 0.05

graph = m.getGraph("ReservoirSplatting")
output_root = Path("phase3-results/presentation")
output_root.mkdir(parents=True, exist_ok=True)

common = {
    "samplesPerPixel": 1,
    "enableTemporalResampling": True,
    "enableSpatialResampling": True,
    "numTimePartitions": 2,
    "scatterBackupMISOption": "Balance",
}

target = (0.0, 0.275, 0.0)
camera_path = [
    (-0.16 + 0.32 * frame / 89.0, 0.275, 1.68737)
    for frame in range(90)
]


def configure_frame_dumper(name):
    output_dir = output_root / name
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.glob("frame.*.pam"):
        path.unlink()

    graph.updatePass("FrameDumper", {
        "outputDir": str(output_dir),
        "outputBase": "frame",
        "frameOffset": 0,
    })
    frame_dumper = graph.getPass("FrameDumper")
    frame_dumper.usePng = False
    return frame_dumper


def set_camera(position):
    m.scene.camera.position = float3(*position)
    m.scene.camera.target = float3(*target)


def warmup(reservoir_splatting):
    reservoir_splatting.resetDynamicObject()
    set_camera(camera_path[0])
    for _ in range(16):
        m.renderFrame()


def capture_camera_segment(name, mode):
    graph.updatePass("ReservoirSplatting", {**common, **mode})
    reservoir_splatting = graph.getPass("ReservoirSplatting")
    frame_dumper = configure_frame_dumper(name)
    warmup(reservoir_splatting)

    if not frame_dumper.startCapture():
        raise RuntimeError("FrameDumper output directory is unavailable.")
    for position in camera_path:
        set_camera(position)
        m.renderFrame()
    frame_dumper.stopCapture()

    print(f"{name}: frames={len(camera_path)}")


capture_camera_segment("camera-gather-robust", {
    "temporalReuse": "GatherOnly",
    "gatherOption": "Robust",
})
capture_camera_segment("camera-scatter-backup", {
    "temporalReuse": "ScatterBackup",
    "gatherOption": "Robust",
})

graph.updatePass("ReservoirSplatting", {**common, "temporalReuse": "MultiScatter"})
reservoir_splatting = graph.getPass("ReservoirSplatting")
frame_dumper = configure_frame_dumper("dynamic-multi-splatting")
warmup(reservoir_splatting)

if not frame_dumper.startCapture():
    raise RuntimeError("FrameDumper output directory is unavailable.")
if not reservoir_splatting.spawnDynamicObject():
    raise RuntimeError("Dynamic sphere node is unavailable.")

dynamic_frames = 0
while reservoir_splatting.dynamicObjectActive:
    m.renderFrame()
    dynamic_frames += 1

frame_dumper.stopCapture()
print(f"dynamic-multi-splatting: frames={dynamic_frames}")

exit()
