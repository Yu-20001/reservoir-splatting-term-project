# Reservoir Splatting Phase 3 Evaluation

## Controlled Setup

- Scene: `data/scenes/reservoir_splatting_dynamic_cornell_box.pyscene`
- Resolution: `960x540`
- Camera shutter speed: `0.05s`
- Samples per pixel: `1`
- Spatial resampling: enabled
- Multi-splat time partitions: `2`
- Dynamic object: rough metallic sphere
- Representative frame: falling-sphere frame `32`
- FrameDumper: disabled during renderer-only measurements

## Automated Capture

Run:

```bash
build/linux-gcc/bin/Release/Mogwai --headless --width 960 --height 540 \
  --script scripts/ReservoirSplattingPhase3Capture.py
```

The script writes GPU profiler results to
`phase3-results/dynamic-object-gpu-summary.csv`. Representative images are
written under `phase3-results/representative-frames/`. Use the
`FrameDumper.dst` output for tone-mapped comparisons.

## Recorded Results

| Mode | Mean | Std. dev. | Min | Max | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| No temporal reuse | `2.281ms` | `0.362ms` | `2.129ms` | `4.436ms` | Naive lower bound |
| `GatherOnly + Robust` | `5.050ms` | `0.333ms` | `2.494ms` | `5.363ms` | Main baseline |
| `ScatterOnly` | `3.168ms` | `0.110ms` | `2.293ms` | `3.258ms` | Single splat |
| `ScatterBackup` | `5.410ms` | `0.392ms` | `2.225ms` | `5.577ms` | Splat with backup |
| `MultiSplatting` | `3.114ms` | `0.111ms` | `2.233ms` | `3.221ms` | Non-zero shutter speed |

The NVIDIA GeForce RTX 5070 Ti Vulkan run completed on 2026-06-07. Each mode
captured `68` valid GPU profiler frames while the sphere fell. Standard
deviation, min, and max describe frame-to-frame variation within this single
falling sequence, not variation across independent benchmark runs. Visual QA
passed for all five tone-mapped representative frames.

## Reference-Based Disocclusion Evaluation

The separate controlled camera-pan experiment under `disocclusion-results/`
uses high-sample references, objective geometry masks, five independent seeds
per evaluated mode, and paired confidence intervals. At the primary `0.02`
world-position threshold:

| Method | Masked NRMSE | Masked log-luminance MAE |
| --- | ---: | ---: |
| `GatherOnly + Robust` | `0.4774` | `0.0385` |
| `ScatterOnly` | `0.8728` | `0.0957` |
| `ScatterBackup` | `0.5965` | `0.0527` |

For this camera pan, robust gather has the lowest reference error on newly
revealed pixels, and ScatterBackup substantially improves over ScatterOnly.
The result does not rank full-frame quality, moving-object behavior, temporal
stability outside the mask, or motion-blur quality.

## Remaining Capture Gates

- Prepare the final narrated presentation from the verified fallback sequence.

## FrameDumper Overhead

Run:

```bash
build/linux-gcc/bin/Release/Mogwai --headless --width 960 --height 540 \
  --script scripts/ReservoirSplattingFrameDumperOverhead.py
```

The separate `MultiSplatting + FrameDumper` PAM capture recorded `69` output
frames with a mean wall-frame time of `9.503ms` (`105.23 FPS`). This includes
GPU readback and file output, so it must not be compared directly with the
renderer-only GPU measurements.

The fallback-video pipeline was verified by encoding the PAM sequence:

```bash
ffmpeg -framerate 30 \
  -i phase3-results/frame-dumper-multi-splatting/frame.%05d.pam \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  phase3-results/dynamic-object-multi-splatting.mp4
```

The verified clip is H.264, `960x540`, `30 FPS`, `69` frames, and `2.30s`.
This is a pipeline check for the falling-sphere segment, not the final
presentation video.

## Presentation Capture

Run:

```bash
build/linux-gcc/bin/Release/Mogwai --headless --width 960 --height 540 \
  --script scripts/ReservoirSplattingPresentationCapture.py
```

The script writes three PAM sequences under `phase3-results/presentation/`:

| Segment | Frames | Purpose |
| --- | ---: | --- |
| `camera-gather-robust` | 90 | Main baseline camera motion |
| `camera-scatter-backup` | 90 | Same camera path with splatting backup |
| `dynamic-multi-splatting` | 69 | Falling-sphere motion-blur segment |

Encode the fallback asset:

```bash
ffmpeg \
  -framerate 30 -i phase3-results/presentation/camera-gather-robust/frame.%05d.pam \
  -framerate 30 -i phase3-results/presentation/camera-scatter-backup/frame.%05d.pam \
  -framerate 30 -i phase3-results/presentation/dynamic-multi-splatting/frame.%05d.pam \
  -filter_complex '[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]' -map '[v]' \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  phase3-results/reservoir-splatting-fallback.mp4
```

The verified fallback asset is H.264, `960x540`, `30 FPS`, `249` frames, and
`8.30s`. Visual QA confirmed camera motion in both comparison segments and the
complete falling-sphere trajectory.
