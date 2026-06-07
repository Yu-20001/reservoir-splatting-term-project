# Reservoir Splatting Submission Notes

## Tested Environment

- GPU: NVIDIA GeForce RTX 5070 Ti
- Graphics API: Vulkan
- Operating system: Arch Linux
- Build preset: `linux-gcc-release`

Build:

```bash
XDG_CACHE_HOME="$PWD/.cache" \
  tools/.packman/cmake/bin/cmake --build --preset linux-gcc-release -j 2
```

Launch the interactive demo:

```bash
build/linux-gcc/bin/Release/Mogwai --script scripts/ReservoirSplatting.py
```

Load:

```text
data/scenes/reservoir_splatting_dynamic_cornell_box.pyscene
```

## Evaluation Commands

```bash
build/linux-gcc/bin/Release/Mogwai --headless --width 960 --height 540 \
  --script scripts/ReservoirSplattingPhase3Capture.py

build/linux-gcc/bin/Release/Mogwai --headless --width 960 --height 540 \
  --script scripts/ReservoirSplattingFrameDumperOverhead.py

build/linux-gcc/bin/Release/Mogwai --headless --width 960 --height 540 \
  --script scripts/ReservoirSplattingPresentationCapture.py
```

Generated evaluation artifacts are written under `phase3-results/`.

## Modifications Relative To The Authors' Repository

- Added Linux portability fixes for build scripts, folder selection, and
  FrameDumper file output.
- Added asynchronous PNG-capture error handling and deferred GPU readback.
- Added scene-node lookup for stable transform updates.
- Added a project-owned Cornell Box scene with one preloaded rough metallic
  sphere.
- Added spawn, reset, simplified gravity, and floor collision controls.
- Added Python hooks and scripts for deterministic benchmark and presentation
  capture.

## Attribution

- Reservoir Splatting implementation and paper:
  Jeffrey Liu, Daqi Lin, Markus Kettunen, Chris Wyman, and Ravi Ramamoorthi,
  "Reservoir Splatting for Temporal Path Resampling and Motion Blur,"
  SIGGRAPH Conference Track, August 2025.
- Falcor 8 framework: NVIDIA.
- Cornell Box scene: upstream Falcor test scene imported from
  `test_scenes/cornell_box.pyscene`.
- Dynamic rough metallic sphere: generated with Falcor
  `TriangleMesh.createSphere()`. No external model asset is used.
- Dynamic rough plastic cube: generated with Falcor
  `TriangleMesh.createCube()`. No external model asset is used.

## Limitations

- The interactive demo supports two preloaded selectable objects and one floor
  collision plane.
- Gravity is simplified; there is no rigid-body rotation, stacking, or
  object-to-object collision.
- Additional ceramic, fabric, and wood objects are deferred.
- Renderer quality still needs a final report comparison using representative
  images. MSE or FLIP remains optional if a reference-render budget is
  available.
- The generated fallback clip is a technical capture asset. The final
  presentation still needs narration and explanatory labels.

## Future Work

- Add per-object collider parameters for more varied preloaded objects.
- Integrate a rigid-body physics library for rotation and collision response.
- Add viewport picking and runtime asset import.
- Evaluate delta materials and caustics with a ReSTIR BDPT-based renderer.
