# Dynamic Object Comparison Figures

Generate both figures from the controlled Phase 3 captures:

```bash
bash scripts/make_report_comparison_figures.sh
```

## Figure 1: Full-Frame Comparison

File: `dynamic-object-five-mode-comparison.png`

Suggested caption:

> Representative frame of the falling-sphere experiment at 1 sample per
> pixel. No temporal reuse exhibits substantially stronger high-frequency
> noise. The temporal reuse modes reduce visible noise, but differ in runtime
> cost and in how historical samples are reused around moving geometry.

## Figure 2: Detail Crops

File: `dynamic-object-detail-crops.png`

The figure enlarges the moving sphere, its boundary, and the newly revealed
region above the tall box.

Suggested caption:

> Enlarged crops from the same falling-sphere frame, emphasizing the
> moving-object and disocclusion boundary. These crops support a qualitative
> comparison of noise and temporal reuse behavior. They do not, without a
> reference image or temporal error metric, establish which reuse method is
> most accurate.

## Defensible Observations

- No temporal reuse is visibly noisier than all four temporal reuse modes.
- Temporal reuse improves visual stability at 1 sample per pixel.
- The moving sphere and newly revealed region are appropriate locations for
  discussing temporal reuse behavior.
- Image quality should be discussed together with GPU frame time.

## Claims Not Yet Supported

- These dynamic-object figures do not prove that one temporal reuse mode is the
  most accurate.
- These dynamic-object figures do not quantify temporal stability.
- Reference-based error for a separate controlled camera-disocclusion
  experiment is reported under `disocclusion-results/`. Its conclusion is
  limited to newly revealed pixels under that camera path and must not be
  transferred directly to the falling-sphere images.

## Figure 3: GPU Frame Time

Generate the GPU frame time chart from the Phase 3 profiler summary:

```bash
python3 scripts/make_gpu_frame_time_figure.py
```

Files:

- `dynamic-object-gpu-frame-time.svg`
- `dynamic-object-gpu-frame-time.png`

Suggested caption:

> Mean GPU frame time with error bars showing one standard deviation for the
> falling-sphere experiment at 960x540 and 1 sample per pixel. Each bar
> summarizes 68 valid GPU profiler frames from one falling sequence.
> ScatterOnly and MultiSplatting add less GPU cost than GatherOnly + Robust
> and ScatterBackup, while disabling temporal reuse is the fastest setting.
> Runtime alone does not establish image quality.

Standard deviation, min, and max describe frame-to-frame variation during one
falling-sphere sequence. They are not confidence intervals across independent
benchmark runs.
