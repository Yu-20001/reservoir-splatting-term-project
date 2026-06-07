# Reservoir Splatting Dynamic Object Benchmark

## Goal

Record reproducible wall-frame times for the falling-sphere demo before adding
optional assets. FrameDumper must remain disabled during renderer benchmarks
because capture I/O is a separate workload.

## Fixed Setup

- Scene: `data/scenes/reservoir_splatting_dynamic_cornell_box.pyscene`
- Spawn position: `(0, 0.45, 0)`
- Resolution: `960x540`
- Camera shutter speed: `0.05s`
- FrameDumper: disabled
- Warmup: wait until shader compilation and scene loading complete

## Capture Procedure

Run the automated headless benchmark from the repository root:

```bash
build/linux-gcc/bin/Release/Mogwai --headless --width 960 --height 540 \
  --script scripts/ReservoirSplattingDynamicBenchmark.py
```

The script writes per-mode CSV files and `dynamic-object-summary.csv` under
`benchmark-results/`.

For an interactive capture, use the equivalent procedure below.

For each mode below:

1. Select the mode and wait for the viewport to stabilize.
2. In the Mogwai Python console, start timing capture:

   ```python
   m.timingCapture.captureFrameTime("dynamic-object-<mode>.csv")
   ```

3. Press `Spawn`.
4. Wait until the sphere reaches the floor.
5. Stop timing capture:

   ```python
   m.timingCapture.captureFrameTime("")
   ```

Use these filenames:

| Mode | Filename |
| --- | --- |
| `GatherOnly + Robust` | `dynamic-object-gather-robust.csv` |
| `ScatterBackup` | `dynamic-object-scatter-backup.csv` |
| `MultiSplatting` | `dynamic-object-multi-splatting.csv` |

Each CSV line is a wall-frame time in seconds. Summarize one run with:

```bash
awk '{ sum += $1 } END { mean = sum / NR; printf "frames=%d mean_ms=%.3f mean_fps=%.2f\n", NR, mean * 1000, 1 / mean }' dynamic-object-<mode>.csv
```

## Record Separately

Run one additional `MultiSplatting` capture with FrameDumper enabled only to
measure fallback-video overhead. Do not compare this result against renderer-only
mode timings.

## Recorded Results

Renderer-only results recorded on 2026-06-01 with an NVIDIA GeForce RTX 5070 Ti
using Vulkan:

| Mode | Frames | Mean wall-frame time | Mean FPS | Notes |
| --- | --- | --- | --- | --- |
| `GatherOnly + Robust` | 69 | `4.518ms` | `221.33` | |
| `ScatterBackup` | 69 | `5.034ms` | `198.66` | |
| `MultiSplatting` | 69 | `2.616ms` | `382.27` | Non-zero shutter speed |
| `MultiSplatting + FrameDumper` | 69 | `9.503ms` | `105.23` | PAM capture overhead; wall-frame time |
