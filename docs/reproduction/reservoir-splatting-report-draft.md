# Interactive Evaluation of Reservoir Splatting under Dynamic Object Motion

## Abstract

Interactive path tracing at low sample counts is noisy because each frame
contains too few paths to estimate illumination reliably. Temporal reuse
reduces this noise by reusing paths from previous frames, but conventional
backprojection can fail when motion reveals surfaces that have no valid
history. This project reproduces the official Reservoir Splatting
implementation on Linux and extends it with an interactive dynamic-object
scene for studying temporal path reuse under object motion, changing
visibility, moving shadows, reflections, and motion blur. The extension adds
preloaded sphere and cube assets, spawn and reset controls, simplified gravity
and floor collision, and reproducible benchmark and capture scripts. Five
temporal reuse configurations are compared at 960x540 and 1 sample per pixel.
ScatterOnly and MultiSplatting require about 3.1 ms per frame in the
falling-sphere benchmark, while GatherOnly + Robust and ScatterBackup require
about 5.1-5.4 ms. A separate reference-based camera-disocclusion experiment
shows that robust gather has the lowest error on newly revealed pixels in the
tested Cornell Box camera pan, while ScatterBackup improves substantially over
ScatterOnly. These results demonstrate that the best reuse strategy depends on
the visibility event being evaluated; runtime alone does not establish image
quality.

## 1. Introduction

Monte Carlo path tracing estimates light transport by sampling paths through a
scene. At the low sample counts required for interactive rendering, its
estimates contain strong spatial and temporal noise. ReSTIR-style methods
improve sample efficiency by maintaining reservoirs and resampling useful
paths across pixels and frames. Temporal resampling is especially valuable
because it increases the effective sample history without tracing the same
number of new paths in every frame.

The difficulty is deciding how a path from the previous frame corresponds to a
pixel in the current frame. Gather or backward-reprojection methods start from
a current pixel and look up history at a reprojected previous-frame position.
This lookup may be approximate near geometry boundaries or invalid when motion
changes visibility. Reservoir Splatting instead forward-projects previous
primary hits into the current frame. Forward projection preserves exact prior
primary hits when they remain visible, and multi-splatting extends the idea
across multiple time samples for motion blur.

This project uses dynamic object motion as an interactive stress case. A
falling object changes the object's projected boundary, reveals and occludes
background surfaces, moves its shadow and reflection, and produces motion blur
when the shutter interval is nonzero. The scene therefore exposes several
conditions in which temporal path reuse decisions become visible.

The project makes four engineering and evaluation contributions:

1. It reproduces the official Reservoir Splatting implementation on Arch Linux
   with an NVIDIA GeForce RTX 5070 Ti using Falcor 8 and Vulkan.
2. It adds an interactive dynamic sphere and cube with spawn controls,
   simplified gravity, and floor collision through existing Falcor scene-node
   transform updates.
3. It establishes reproducible GPU benchmark, screenshot, video, geometry, and
   high-sample reference capture pipelines.
4. It compares temporal reuse modes through renderer-only GPU timing,
   qualitative dynamic-object images, and a reference-based disocclusion
   experiment with repeated seeds and confidence intervals.

The Reservoir Splatting algorithm is prior work. The contribution of this
project is its Linux reproduction, interactive extension, controlled
experiments, and evidence-based evaluation.

## 2. Background and Related Work

### 2.1 Reservoir Resampling

Reservoir sampling compactly represents a selected sample and its accumulated
weight. Resampled Importance Sampling (RIS), ReSTIR, and Generalized Resampled
Importance Sampling (GRIS) use reservoirs to combine candidate paths from
different domains while preserving a valid estimator. Spatial reuse combines
nearby pixels, while temporal reuse combines information across frames.

Temporal reuse can greatly reduce noise at low samples per pixel, but it
depends on a correspondence between frames. A current surface point may move,
become occluded, or be newly revealed. Reusing unrelated history in these
cases introduces error, while rejecting too much history loses the benefit of
temporal accumulation.

### 2.2 Gather and Splat

The conceptual distinction used throughout this report is:

```text
Gather / backward projection:
current pixel -> previous-frame location -> historical sample

Splat / forward projection:
previous primary hit -> current-frame pixel -> reused sample
```

Gather-based reuse can provide a fallback for a newly revealed current pixel,
but its reprojected primary hit may be approximate. Reservoir Splatting
forwards the prior frame's exact primary hit into the current frame. A single
prior hit may splat to one current pixel, while multi-splatting projects at
several time samples to support motion blur. ScatterBackup combines splatting
with a gather fallback where no useful forward-splatted history arrives.

The evaluated implementation builds on the official Reservoir Splatting
renderer, GRIS, Area ReSTIR, and NVIDIA Falcor 8. The renderer uses a
reconnection shift after the primary hit and therefore does not support delta
materials in the tested configuration.

## 3. System Design

The interactive extension follows this update path:

```text
Cornell Box + preloaded dynamic objects
                  |
Dynamic object controller
select / spawn / reset / gravity / floor collision
                  |
Scene::updateNodeTransform()
                  |
Falcor scene graph and TLAS update
                  |
ReservoirSplatting render pass
                  |
benchmark / screenshot / geometry / FrameDumper capture
```

The sphere and cube are created in a project-owned `.pyscene` and initially
placed outside the room. This design avoids runtime mesh insertion and keeps
the extension within Falcor's established scene graph. After scene load,
`Scene::findNodeIDByName()` locates the dynamic nodes. Each simulation update
uses `Scene::updateNodeTransform()`, which triggers the existing scene graph
and acceleration-structure synchronization path.

The object controller exposes an object selector, editable spawn position,
spawn and reset actions, simplified gravitational acceleration, and collision
against one horizontal floor plane. The sphere uses a rough metallic material
and the cube uses a rough plastic material. Both avoid delta materials because
the reproduced path-reuse configuration does not support them.

The capture system separates renderer performance from output overhead. GPU
profiler measurements disable FrameDumper. Screenshot and video pipelines use
FrameDumper only when output is required. A separate geometry capture exports
world position, motion vectors, and validity masks to construct objective
disocclusion masks.

## 4. Implementation

The original repository provides the Reservoir Splatting render pass and its
temporal reuse modes. This project adds:

- Linux build and runtime portability fixes.
- Linux-compatible folder selection and FrameDumper behavior.
- Deferred readback, asynchronous PNG error handling, and Python capture hooks.
- A dynamic Cornell Box scene with preloaded sphere and cube nodes.
- Dynamic object selection, spawn position, spawn, and reset controls.
- Simplified gravity and floor-plane collision.
- Automated renderer-only GPU timing and representative-frame capture.
- Fixed camera-path capture with deterministic initial seeds.
- Geometry capture, high-sample reference capture, masked error analysis,
  confidence intervals, sensitivity analysis, and report figure generation.

The evaluated temporal configurations are:

| Mode | Role in this report |
| --- | --- |
| No temporal reuse | Runtime lower bound and noisy visual baseline |
| GatherOnly + Robust | Backprojection-based baseline |
| ScatterOnly | Single forward-splat configuration |
| ScatterBackup | Forward splat with gather fallback |
| MultiSplatting | Multi-time-sample splatting for motion blur |

The high-sample reference experiment reports HDR normalized root mean squared
error (NRMSE), which is derived from MSE but normalized by reference RMS to
make values comparable across masked frames. It also reports log-luminance
mean absolute error (MAE), signed luminance bias, and non-finite pixel rate.
FLIP is not used because its result depends on a specified display transform
and viewing configuration; the present experiment instead evaluates linear HDR
output and log luminance directly.

## 5. Experimental Design

### 5.1 Platform and Shared Settings

| Variable | Value |
| --- | --- |
| GPU | NVIDIA GeForce RTX 5070 Ti, 16 GB |
| Driver | NVIDIA `595.58.03` |
| Operating system | Arch Linux |
| Graphics API / framework | Vulkan / Falcor 8 |
| Resolution | `960x540` |
| Samples per pixel | `1` for evaluated modes |
| Spatial resampling | Enabled |

All comparisons use the same scene, rendering settings, object trajectory or
camera path, and resolution within their experiment. FrameDumper is disabled
for renderer-only GPU timing.

### 5.2 Falling-Sphere Performance and Visual Experiment

The falling-sphere experiment uses a rough metallic sphere, a shutter speed of
`0.05 s`, and two multi-splat time partitions. GPU timings contain 68 valid
profiler frames from one falling sequence per mode. Representative images use
falling-sphere frame 32.

This experiment answers two questions: how much GPU time each configuration
requires during object motion, and what visible differences appear in a
controlled representative frame. Its frame-to-frame standard deviations are
not confidence intervals across independent benchmark runs.

### 5.3 Reference-Based Camera-Disocclusion Experiment

The objective quality experiment isolates newly revealed surfaces from motion
blur by setting shutter speed to zero. Three modes follow an identical
90-frame horizontal camera path: GatherOnly + Robust, ScatterOnly, and
ScatterBackup. Each mode has five independent initial seeds. Ten target frames
are evaluated along the path.

For each target frame, two independent references accumulate 1024 one-sample
frames. Their average is used as the high-sample reference, and their
difference estimates the reference noise floor.

A current pixel is marked disoccluded when its motion-vector-reprojected
coordinate is outside the previous frame, maps to no previous geometry, or
has a previous world position differing from the current world position by
more than `0.02` scene units. The mask is dilated by one pixel to include
immediate boundary behavior. Thresholds `0.01` and `0.04` are also analyzed to
check sensitivity.

The primary metrics are computed only inside this mask:

- HDR RGB NRMSE.
- Log-luminance MAE.
- Signed luminance bias.
- Masked and full-frame non-finite pixel rates.
- Paired 95% confidence intervals over five independent seeds.

## 6. Performance Results

| Mode | Mean GPU time | Std. dev. | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| No temporal reuse | `2.281 ms` | `0.362 ms` | `2.129 ms` | `4.436 ms` |
| GatherOnly + Robust | `5.050 ms` | `0.333 ms` | `2.494 ms` | `5.363 ms` |
| ScatterOnly | `3.168 ms` | `0.110 ms` | `2.293 ms` | `3.258 ms` |
| ScatterBackup | `5.410 ms` | `0.392 ms` | `2.225 ms` | `5.577 ms` |
| MultiSplatting | `3.114 ms` | `0.111 ms` | `2.233 ms` | `3.221 ms` |

No temporal reuse is the fastest configuration, but its representative image
is visibly noisier. ScatterOnly and MultiSplatting have similar measured cost
and are substantially less expensive than GatherOnly + Robust and
ScatterBackup. ScatterBackup is the most expensive tested configuration
because it combines forward splatting with backup reuse.

FrameDumper overhead was measured separately. MultiSplatting with PAM output
recorded 69 frames at a mean wall-frame time of `9.503 ms` (`105.23 FPS`).
This value includes readback and file output and is not directly comparable to
renderer-only GPU timings.

## 7. Visual and Reference-Based Results

The falling-sphere full-frame and crop figures show that disabling temporal
reuse produces substantially stronger high-frequency noise at 1 sample per
pixel. The moving sphere boundary and the newly revealed region above the tall
box provide useful locations for qualitative inspection. These images show
that temporal reuse changes the visible result, but a single image without a
reference cannot rank the accuracy or temporal stability of the reuse modes.

The reference-based camera-disocclusion experiment provides an objective
result for a narrower question:

| Method | Masked HDR NRMSE | Masked log-luminance MAE |
| --- | ---: | ---: |
| GatherOnly + Robust | `0.4774` | `0.0385` |
| ScatterOnly | `0.8728` | `0.0957` |
| ScatterBackup | `0.5965` | `0.0527` |

The mean reference noise floor is approximately `0.0278` NRMSE and `0.0035`
log-luminance MAE. All test and reference outputs contain zero non-finite
pixels.

Paired seed-level comparisons show separated confidence intervals:

- GatherOnly has `0.0572` lower log-luminance MAE than ScatterOnly, with a 95%
  confidence interval of `[0.0562, 0.0581]`.
- GatherOnly has `0.0141` lower log-luminance MAE than ScatterBackup, with a
  95% confidence interval of `[0.0135, 0.0147]`.
- ScatterBackup has `0.0430` lower log-luminance MAE than ScatterOnly, with a
  95% confidence interval of `[0.0424, 0.0437]`.

The ranking remains unchanged at world-position thresholds `0.01`, `0.02`,
and `0.04`. For this controlled camera pan, robust gather therefore produces
the lowest reference error on immediately newly revealed pixels.
ScatterBackup's improvement over ScatterOnly confirms the value of a gather
fallback when no useful forward-splatted history exists.

This result does not contradict the motivation for splatting. A newly revealed
pixel has no corresponding previous-frame primary hit to forward splat, so
ScatterOnly is expected to be weak in this specific region. The result does
not establish that GatherOnly has the best full-frame quality, temporal
stability outside the mask, dynamic-object behavior, or motion-blur quality.

## 8. Limitations, Conclusion, and Future Work

### 8.1 Limitations

- The interactive demo contains only a preloaded sphere and cube.
- The simplified simulation omits rotation, stacking, and object-to-object
  collision and uses one floor collision plane.
- Delta materials, glass, and caustics are outside the evaluated renderer
  configuration.
- GPU timing uses one falling sequence per mode rather than repeated benchmark
  runs.
- The objective experiment evaluates camera-driven disocclusion in one Cornell
  Box path, not moving-object disocclusion or motion blur.
- The report uses HDR NRMSE and log-luminance MAE rather than display-referred
  FLIP.
- The scene and resolution range is limited.

### 8.2 Conclusion

This project successfully reproduces the official Reservoir Splatting renderer
on an Arch Linux RTX 5070 Ti system and extends it with an interactive dynamic
geometry demonstration. The extension uses existing Falcor node-transform and
acceleration-structure update paths, and its scripts provide reproducible
renderer benchmarks, image captures, video captures, geometry masks, and
high-sample references.

The measured results expose a meaningful tradeoff. ScatterOnly and
MultiSplatting are less expensive than the robust gather and backup
configurations in the falling-sphere benchmark, while temporal reuse visibly
reduces noise relative to disabling reuse. In a targeted camera-disocclusion
experiment, robust gather is most accurate on newly revealed pixels and
ScatterBackup substantially improves over ScatterOnly. Temporal reuse methods
must therefore be evaluated against the visibility event and quality criterion
they are intended to handle, rather than ranked by frame time or one
representative image alone.

### 8.3 Future Work

- Capture high-sample references for moving-object disocclusion and nonzero
  shutter speed.
- Add display-referred FLIP with a documented tone mapper and viewing setup.
- Repeat GPU timing across independent runs and report confidence intervals.
- Evaluate more scenes, object velocities, shutter speeds, and resolutions.
- Add rigid-body rotation, collision response, and runtime asset import.
- Explore delta materials and caustics with a compatible ReSTIR BDPT approach.

## Figure Plan and Evidence

| Figure | Artifact | Supported conclusion |
| --- | --- | --- |
| Gather vs. splat concept | To be drawn from Section 2 diagram | Explains correspondence direction; not an empirical result |
| System architecture | To be drawn from Section 3 diagram | Documents project data flow; not a performance claim |
| Five-mode falling sphere | `report-assets/figures/dynamic-object-five-mode-comparison.png` | No temporal reuse is visibly noisier; single frame cannot rank accuracy |
| Dynamic-object crops | `report-assets/figures/dynamic-object-detail-crops.png` | Identifies motion/disocclusion regions for qualitative discussion |
| GPU frame time | `report-assets/figures/dynamic-object-gpu-frame-time.png` | Compares runtime for one falling sequence; does not establish quality |
| Disocclusion error summary | `disocclusion-results/figures/disocclusion-error-summary.png` | Robust gather has lowest masked log-luminance error in the controlled camera pan |
| Error over camera path | `disocclusion-results/figures/disocclusion-error-over-time.png` | Shows the ranking persists across sampled path frames |
| Reference and mask example | `disocclusion-results/figures/disocclusion-representative-frame-44.png` | Shows what pixels and reference are used; one frame is illustrative, not the aggregate result |

## References

1. J. Liu, D. Lin, M. Kettunen, C. Wyman, and R. Ramamoorthi, "Reservoir
   Splatting for Temporal Path Resampling and Motion Blur," SIGGRAPH Conference
   Track, 2025.
2. D. Lin et al., "Generalized Resampled Importance Sampling: Foundations of
   ReSTIR," SIGGRAPH, 2022.
3. S. Zhang et al., "Area ReSTIR: Resampling for Real-Time Defocus and
   Antialiasing," SIGGRAPH Asia, 2024.
4. NVIDIA, "Falcor: Real-Time Rendering Framework," version 8.
