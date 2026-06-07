import os
from pathlib import Path

from falcor import *


def create_experiment_graph():
    graph = RenderGraph("ReservoirSplattingDisocclusion")

    vbuffer = createPass(
        "VBufferRT",
        {
            "samplePattern": "Center",
            "sampleCount": 1,
            "useAlphaTest": True,
            "useDOF": False,
        },
    )
    graph.addPass(vbuffer, "VBufferRT")

    reservoir = createPass(
        "ReservoirSplatting",
        {
            "samplesPerPixel": 1,
            "enableTemporalResampling": True,
            "enableSpatialResampling": True,
            "temporalReuse": "ScatterOnly",
            "gatherOption": "Robust",
            "scatterBackupMISOption": "Balance",
        },
    )
    graph.addPass(reservoir, "ReservoirSplatting")

    accumulate = createPass("AccumulatePass", {"enabled": False, "precisionMode": "Single"})
    graph.addPass(accumulate, "AccumulatePass")

    graph.addEdge("VBufferRT.vbuffer", "ReservoirSplatting.vbuffer")
    graph.addEdge("VBufferRT.mvec", "ReservoirSplatting.mvec")
    graph.addEdge("ReservoirSplatting.color", "AccumulatePass.input")

    graph.markOutput("AccumulatePass.output")
    graph.markOutput("VBufferRT.posW")
    graph.markOutput("VBufferRT.mvec")
    graph.markOutput("VBufferRT.mask")
    return graph


graph = create_experiment_graph()
m.addGraph(graph)
m.resizeFrameBuffer(960, 540)
m.loadScene("data/scenes/reservoir_splatting_dynamic_cornell_box.pyscene")
m.scene.camera.shutterSpeed = 0.0

output_root = Path(os.environ.get("DISOCCLUSION_OUTPUT_ROOT", "disocclusion-results"))
capture_dir = output_root / "captures"
capture_dir.mkdir(parents=True, exist_ok=True)
for path in capture_dir.glob("*.exr"):
    path.unlink()
m.frameCapture.outputDir = capture_dir.resolve()
m.frameCapture.captureAllOutputs = False

reservoir = graph.getPass("ReservoirSplatting")
accumulate = graph.getPass("AccumulatePass")

start_pos = (-0.16, 0.275, 1.68737)
end_pos = (0.16, 0.275, 1.68737)
target = (0.0, 0.275, 0.0)
up = (0.0, 1.0, 0.0)
frame_count = 90
target_frames = [
    int(frame)
    for frame in os.environ.get("DISOCCLUSION_TARGET_FRAMES", "8,17,26,35,44,53,62,71,80,89").split(",")
]
geometry_frames = sorted(set(target_frames + [frame - 1 for frame in target_frames]))
run_seeds = [int(seed) for seed in os.environ.get("DISOCCLUSION_RUN_SEEDS", "101,1009,2027,4093,8089").split(",")]
reference_seeds = [int(seed) for seed in os.environ.get("DISOCCLUSION_REFERENCE_SEEDS", "50021,90001").split(",")]
reference_frames = int(os.environ.get("DISOCCLUSION_REFERENCE_FRAMES", "1024"))
warmup_frames = int(os.environ.get("DISOCCLUSION_WARMUP_FRAMES", "24"))

camera_path = [
    (
        start_pos[0] + (end_pos[0] - start_pos[0]) * frame / (frame_count - 1),
        start_pos[1],
        start_pos[2],
    )
    for frame in range(frame_count)
]

common = {
    "samplesPerPixel": 1,
    "maxSurfaceBounces": 2,
    "maxDiffuseBounces": 1,
    "maxSpecularBounces": 1,
    "maxTransmissionBounces": 0,
    "enableTemporalResampling": True,
    "enableSpatialResampling": True,
    "gatherOption": "Robust",
    "scatterBackupMISOption": "Balance",
}

modes = [
    ("gather-robust", {"temporalReuse": "GatherOnly"}),
    ("scatter-only", {"temporalReuse": "ScatterOnly"}),
    ("scatter-backup", {"temporalReuse": "ScatterBackup"}),
]


def set_camera(position):
    m.scene.camera.position = float3(*position)
    m.scene.camera.target = float3(*target)
    m.scene.camera.up = float3(*up)


def capture(name):
    m.frameCapture.baseFilename = name
    m.frameCapture.capture()


def warmup(seed):
    set_camera(camera_path[0])
    reservoir.reset()
    reservoir.seed = seed
    for _ in range(warmup_frames):
        m.renderFrame()


# Capture geometry buffers once for objective reprojection-based masks.
graph.updatePass(
    "ReservoirSplatting",
    {
        **common,
        "enableTemporalResampling": False,
        "enableSpatialResampling": False,
    },
)
warmup(17)
for frame, position in enumerate(camera_path):
    set_camera(position)
    m.renderFrame()
    if frame in geometry_frames:
        capture(f"geometry-frame-{frame:02d}")

graph.unmarkOutput("VBufferRT.posW")
graph.unmarkOutput("VBufferRT.mvec")
graph.unmarkOutput("VBufferRT.mask")

# Capture independent stochastic runs for each temporal reuse method.
for mode_name, mode in modes:
    graph.updatePass("ReservoirSplatting", {**common, **mode})
    accumulate.enabled = False
    for seed in run_seeds:
        warmup(seed)
        for frame, position in enumerate(camera_path):
            set_camera(position)
            m.renderFrame()
            if frame in target_frames:
                capture(f"test-{mode_name}-seed-{seed}-frame-{frame:02d}")

# Capture two independent high-sample references at each target camera.
graph.updatePass(
    "ReservoirSplatting",
    {
        **common,
        "samplesPerPixel": 1,
        "enableTemporalResampling": False,
        "enableSpatialResampling": False,
    },
)
accumulate.enabled = True
for frame in target_frames:
    set_camera(camera_path[frame])
    for seed in reference_seeds:
        reservoir.reset()
        reservoir.seed = seed
        for _ in range(4):
            m.renderFrame()
        accumulate.reset()
        for _ in range(reference_frames):
            m.renderFrame()
        capture(f"reference-seed-{seed}-frame-{frame:02d}")

print(
    f"Disocclusion experiment complete: target_frames={target_frames}, "
    f"runs_per_mode={len(run_seeds)}, reference_spp={reference_frames}"
)
exit()
