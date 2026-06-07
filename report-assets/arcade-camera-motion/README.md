# Arcade Camera-Motion Comparison

> Superseded exploratory capture. Do not use this single-frame comparison as
> report evidence. The reference-based experiment under
> `disocclusion-results/` provides objective masks, high-sample references,
> repeated runs, and confidence intervals.

Generate the capture with GPU access:

```bash
build/linux-gcc/bin/Release/Mogwai --headless --width 960 --height 540 \
  --script scripts/ReservoirSplattingArcadeCameraCapture.py
```

Generate the report figures and pairwise MAE table:

```bash
bash scripts/make_arcade_camera_motion_figure.sh
```

## Controlled Setup

- Scene: `Arcade/Arcade.pyscene`
- Resolution: `960x540`
- Camera path: identical 90-frame horizontal pan for all modes
- Shutter speed: `0.05s`
- Samples per pixel: `4`
- Surface bounces: `2`
- Diffuse bounces: `0`
- Specular bounces: `1`
- Transmission bounces: `0`
- Selected representative frame: `85`

The reduced-bounce setup suppresses unrelated full-GI noise so motion and
temporal reuse behavior are easier to inspect. It is not a full-GI quality
comparison.

## Frame Selection

Pairwise full-frame MAE was used only as a candidate-ranking heuristic. The
largest average differences cluster around frames `81-89`, where the camera pan
reveals a new region along the left edge. Frame `85` was selected because it is
inside this high-difference interval without being the final path endpoint.

## Suggested Caption

> Arcade camera-motion comparison at frame 85 of an identical 90-frame camera
> pan. The enlarged left-edge crop contains newly revealed geometry and is the
> most relevant region for inspecting temporal reuse under disocclusion. The
> images provide a qualitative comparison; without a reference image or
> temporal error metric, they do not establish which method is most accurate.

## Defensible Observations

- All three methods were captured under the same scene, path, and rendering
  settings.
- The left edge is a meaningful disocclusion region created by camera motion.
- Pairwise image differences increase near the end of the pan as more geometry
  becomes visible.
- At frame `85`, GatherOnly and ScatterBackup have similar visible brightness
  in the newly revealed region, while MultiSplatting is visibly darker. A
  reference is required before interpreting that difference as error.

## Claims Not Yet Supported

- Pairwise MAE is not an accuracy metric because no method is a reference.
- A single selected frame cannot quantify temporal stability.
- The reduced-bounce Arcade capture should not be presented as a full-GI
  quality result.
