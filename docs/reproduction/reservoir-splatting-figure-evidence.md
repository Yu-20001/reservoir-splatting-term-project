# Reservoir Splatting Figure Evidence Matrix

This document records what each report artifact can and cannot support. It is
the claim boundary used when writing captions, results, and conclusions.

| Artifact | Evidence type | Supported claims | Unsupported claims |
| --- | --- | --- | --- |
| `report-assets/figures/dynamic-object-five-mode-comparison.png` | Controlled representative frame | No temporal reuse is visibly noisier at 1 spp; all modes render the same falling-sphere state | Which temporal mode is most accurate or temporally stable |
| `report-assets/figures/dynamic-object-detail-crops.png` | Enlarged qualitative crops | Sphere boundary and newly revealed region are useful inspection areas; reuse modes produce visible differences | Accuracy ranking without a reference; sequence-wide stability |
| `report-assets/figures/dynamic-object-gpu-frame-time.png` | GPU profiler timing, 68 frames from one sequence per mode | No reuse is fastest; ScatterOnly and MultiSplatting cost less than GatherOnly + Robust and ScatterBackup in this run | Image quality; confidence across independent benchmark runs |
| `disocclusion-results/figures/disocclusion-error-summary.png` | Reference-based repeated-seed aggregate | GatherOnly + Robust has the lowest masked log-luminance MAE for the controlled camera pan; ScatterBackup improves over ScatterOnly | Best full-frame, dynamic-object, or motion-blur quality |
| `disocclusion-results/figures/disocclusion-error-over-time.png` | Reference-based per-target-frame metric | The aggregate method ranking is not caused by one selected target frame | Continuous-frame temporal stability or performance outside the mask |
| `disocclusion-results/figures/disocclusion-representative-frame-44.png` | Illustrative reference, methods, and mask | Shows the high-sample reference and the pixels included by the objective mask | Aggregate method ranking from this frame alone |
| `report-assets/arcade-camera-motion/arcade-camera-motion-frame-85.png` | Exploratory pairwise comparison | Camera motion creates a visible left-edge disocclusion region | Accuracy ranking because no high-sample reference is present |

## Quantitative Claim Boundary

The primary reference-based result is limited to immediately disoccluded pixels
under one zero-shutter Cornell Box camera pan. At the primary `0.02`
world-position threshold:

| Method | Masked NRMSE | Masked log-luminance MAE |
| --- | ---: | ---: |
| GatherOnly + Robust | `0.4774` | `0.0385` |
| ScatterOnly | `0.8728` | `0.0957` |
| ScatterBackup | `0.5965` | `0.0527` |

The ranking is unchanged at thresholds `0.01`, `0.02`, and `0.04`. The result
supports the value of robust gather and gather fallback on newly revealed
pixels. It does not rank full-frame quality, moving-object disocclusion,
temporal stability outside the mask, or motion blur.

## Caption Rule

Every empirical figure caption should state:

1. The scene, event, and relevant fixed settings.
2. Whether the evidence is qualitative, runtime-only, or reference-based.
3. The narrow conclusion supported by the figure.
4. Any important claim that the figure alone cannot establish.
