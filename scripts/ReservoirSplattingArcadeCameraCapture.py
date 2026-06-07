from pathlib import Path

m.script("scripts/ReservoirSplatting.py")
m.resizeFrameBuffer(960, 540)
m.loadScene("Arcade/Arcade.pyscene")

graph = m.getGraph("ReservoirSplatting")
output_root = Path("phase3-results/arcade-camera-motion")
output_root.mkdir(parents=True, exist_ok=True)

m.scene.camera.shutterSpeed = 0.05
m.scene.camera.focalLength = 21.0

start_pos = (-1.48, 1.8430896997451783, 2.4423341751098635)
end_pos = (-0.78, 1.8430896997451783, 2.4423341751098635)
target = (-0.7014234066009522, 1.4863656759262086, 1.6192376613616944)
up = (-0.3762371838092804, 0.6345208287239075, 0.6751033663749695)
frame_count = 90

camera_path = [
    (
        start_pos[0] + (end_pos[0] - start_pos[0]) * frame / (frame_count - 1),
        start_pos[1],
        start_pos[2],
    )
    for frame in range(frame_count)
]

common = {
    "samplesPerPixel": 4,
    "maxSurfaceBounces": 2,
    "maxDiffuseBounces": 0,
    "maxSpecularBounces": 1,
    "maxTransmissionBounces": 0,
    "enableTemporalResampling": True,
    "enableSpatialResampling": True,
    "numTimePartitions": 2,
    "scatterBackupMISOption": "Balance",
}

modes = [
    ("gather-robust", {"temporalReuse": "GatherOnly", "gatherOption": "Robust"}),
    ("scatter-backup", {"temporalReuse": "ScatterBackup", "gatherOption": "Robust"}),
    ("multi-splatting", {"temporalReuse": "MultiScatter"}),
]


def set_camera(position):
    m.scene.camera.position = float3(*position)
    m.scene.camera.target = float3(*target)
    m.scene.camera.up = float3(*up)


def configure_frame_dumper(name):
    output_dir = output_root / name
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.glob("frame.*.pam"):
        path.unlink()

    graph.updatePass(
        "FrameDumper",
        {
            "outputDir": str(output_dir),
            "outputBase": "frame",
            "frameOffset": 0,
        },
    )
    frame_dumper = graph.getPass("FrameDumper")
    frame_dumper.usePng = False
    return frame_dumper


for name, mode in modes:
    graph.updatePass("ReservoirSplatting", {**common, **mode})
    reservoir_splatting = graph.getPass("ReservoirSplatting")
    reservoir_splatting.reset()
    frame_dumper = configure_frame_dumper(name)

    set_camera(camera_path[0])
    for _ in range(24):
        m.renderFrame()

    if not frame_dumper.startCapture():
        raise RuntimeError(f"FrameDumper could not start for {name}.")

    for position in camera_path:
        set_camera(position)
        m.renderFrame()

    frame_dumper.stopCapture()
    captured = len(list((output_root / name).glob("frame.*.pam")))
    print(f"{name}: captured {captured} frames")

exit()
