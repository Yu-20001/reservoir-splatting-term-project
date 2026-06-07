# Reservoir Splatting Dynamic Object Smoke Test

## Setup

- Build: PASS (`cmake --build --preset linux-gcc-release -j 2`)
- Scene syntax and release data deployment: PASS
- Scene load: PASS
- Dynamic sphere and cube node lookup: PASS

## Runtime

- Spawn sphere: PASS
- Gravity update: PASS
- Floor collision: PASS
- Reset sphere: PASS
- Spawn rough plastic cube: PASS
- Reset cube: PASS
- Repeated spawn without reset: PASS
- Switch object type and spawn: PASS
- GatherOnly + Robust during motion: PASS
- ScatterBackup during motion: PASS
- MultiSplatting during motion: PASS
- FrameDumper capture during motion: PASS with expected FPS reduction while GPU readback, PNG compression, and disk writes are active
- Moving-object shadows and reflections: PASS

## Issues

- FrameDumper PNG capture aborted Mogwai while testing MultiSplatting. The system coredump showed an uncaught exception from `Bitmap::saveImage()` on the asynchronous PNG writer thread.
- The first fix made PNG saving synchronous to surface errors safely, but runtime testing showed a regression to about 3.8 FPS due to serialized PNG compression.
- FrameDumper now uses a portable `frame-dump` default directory and creates it before capture. Asynchronous PNG saving is restored, with exceptions handled inside `Texture::captureToFile()` worker tasks so failed writes are logged without aborting Mogwai.
- A second runtime test still showed an FPS drop during MultiSplatting capture. `Texture::captureToFile()` was still completing a synchronous GPU readback before dispatching the PNG writer. It now queues the existing `ReadTextureTask` immediately and defers the fence wait, readback map, and PNG write to the worker.
- The final runtime retest wrote PNG files without crashing. MultiSplatting capture still reduces FPS because each captured frame requires GPU readback, PNG compression, and disk I/O. This is expected capture overhead.
