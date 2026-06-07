# Reference-Based Camera Disocclusion Experiment

## Research Question

When camera motion reveals previously occluded pixels, which temporal reuse
method produces the lowest error relative to a high-sample reference?

## Controlled Variables

- Scene: `data/scenes/reservoir_splatting_dynamic_cornell_box.pyscene`
- Resolution: `960x540`
- Camera motion: identical 90-frame horizontal path
- Shutter speed: `0`, isolating disocclusion from motion blur
- Samples per pixel: `1` for evaluated methods
- Surface/diffuse/specular bounces: `2/1/1`
- Spatial resampling: enabled and identical for all evaluated methods
- Evaluated methods: `GatherOnly + Robust`, `ScatterOnly`, `ScatterBackup`
- Independent runs per method: `5`
- Target frames: `8, 17, ..., 89`
- Reference: two independent `1024`-frame, `1 spp` accumulations per target
  frame

## Objective Disocclusion Mask

For each current-frame pixel, the VBuffer motion vector maps it into the
previous frame. The pixel is marked disoccluded if:

- The reprojected coordinate is outside the previous frame.
- The previous frame contains no geometry at that coordinate.
- The reprojected previous world position differs from the current world
  position by more than `0.02` scene units.

The resulting mask is dilated by one pixel to include immediate boundary
behavior.

## Metrics

All metrics are computed only inside the disocclusion mask:

- HDR RGB normalized RMSE.
- Log-luminance mean absolute error.
- Signed luminance bias.
- Non-finite pixel rate, reported as a reliability failure rather than ignored.
- Per-seed metrics averaged across target frames.
- Paired 95% confidence intervals over the five independent seeds.
- Reference noise floor from the two independent reference accumulations.

## Reproduction

Build after adding the initial-seed Python binding:

```bash
tools/.packman/cmake/bin/cmake --build --preset linux-gcc-release -j 2
```

Capture with GPU access:

```bash
build/linux-gcc/bin/Release/Mogwai --headless --width 960 --height 540 \
  --script scripts/ReservoirSplattingDisocclusionExperiment.py
```

Analyze:

```bash
python scripts/analyze_disocclusion_experiment.py
```

## Interpretation Rule

A method can be claimed to handle newly revealed pixels more accurately only
if its masked reference error is lower and its confidence interval is separated
from competing methods by more than the measured reference noise floor.

## Recorded Results

Primary mask threshold: `0.02` scene units.

| Method | Masked NRMSE | Masked log-luminance MAE |
| --- | ---: | ---: |
| `GatherOnly + Robust` | `0.4774` | `0.0385` |
| `ScatterOnly` | `0.8728` | `0.0957` |
| `ScatterBackup` | `0.5965` | `0.0527` |

The mean reference noise floor is approximately `0.0278` NRMSE and `0.0035`
log-luminance MAE. All evaluated outputs and references contain zero non-finite
pixels.

Paired seed-level comparisons:

- GatherOnly has lower log-luminance MAE than ScatterOnly by `0.0572`; the 95%
  confidence interval is `[0.0562, 0.0581]`.
- GatherOnly has lower log-luminance MAE than ScatterBackup by `0.0141`; the
  95% confidence interval is `[0.0135, 0.0147]`.
- ScatterBackup has lower log-luminance MAE than ScatterOnly by `0.0430`; the
  95% confidence interval is `[0.0424, 0.0437]`.

The method ranking is unchanged for world-position thresholds `0.01`, `0.02`,
and `0.04`.

## Supported Conclusion

For this controlled Cornell Box camera pan, robust gather produces the lowest
reference error on newly revealed pixels. ScatterBackup substantially improves
over ScatterOnly, confirming the value of a gather fallback where no useful
forward-splatted history exists. ScatterOnly has the highest disocclusion error
because newly visible pixels do not have a corresponding prior-frame primary
hit to splat.

This conclusion is specific to immediately disoccluded pixels under camera
motion. It does not claim that GatherOnly has the best full-frame quality, the
best temporal stability outside the mask, or the best behavior under motion
blur.

## Report Figures

- `figures/disocclusion-error-summary.png`
- `figures/disocclusion-error-over-time.png`
- `figures/disocclusion-representative-frame-44.png`
