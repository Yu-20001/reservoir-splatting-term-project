from falcor import *


def render_graph_ReservoirSplatting_ReproScatterOnly():
    g = RenderGraph("ReservoirSplatting_ReproScatterOnly")

    VBufferParams = {
        'samplePattern': "Center",
        'sampleCount': 1,
        'useAlphaTest': True,
        'useDOF': False,
    }

    ReservoirSplattingParams = {
        'samplesPerPixel': 1,
        'fixedSeed': 1,
        'enableTemporalResampling': True,
        'enableSpatialResampling': False,
        'temporalReuse': "ScatterOnly",
        'numTimePartitions': 2,
        'gatherOption': "Fast",
    }

    VBufferRT = createPass("VBufferRT", VBufferParams)
    g.addPass(VBufferRT, "VBufferRT")

    ReservoirSplatting = createPass("ReservoirSplatting", ReservoirSplattingParams)
    g.addPass(ReservoirSplatting, "ReservoirSplatting")

    AccumulatePass = createPass("AccumulatePass", {'enabled': False, 'precisionMode': 'Single'})
    g.addPass(AccumulatePass, "AccumulatePass")

    ToneMapper = createPass("ToneMapper", {'autoExposure': False, 'exposureCompensation': 0.0})
    g.addPass(ToneMapper, "ToneMapper")

    FrameDumper = createPass("FrameDumper")
    g.addPass(FrameDumper, "FrameDumper")

    g.addEdge("VBufferRT.vbuffer", "ReservoirSplatting.vbuffer")
    g.addEdge("VBufferRT.mvec", "ReservoirSplatting.mvec")
    g.addEdge("ReservoirSplatting.color", "AccumulatePass.input")
    g.addEdge("AccumulatePass.output", "ToneMapper.src")
    g.addEdge("ToneMapper.dst", "FrameDumper.src")

    g.markOutput("FrameDumper.dst")
    g.markOutput("AccumulatePass.output")
    return g


ReservoirSplatting_ReproScatterOnly = render_graph_ReservoirSplatting_ReproScatterOnly()
try:
    m.addGraph(ReservoirSplatting_ReproScatterOnly)
except NameError:
    None
