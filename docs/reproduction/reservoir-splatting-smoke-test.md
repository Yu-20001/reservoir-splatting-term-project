# Reservoir Splatting Smoke Test Record

## Upstream Checkout

| Item | Value |
| --- | --- |
| Upstream URL | `https://github.com/Jebbly/Reservoir-Splatting` |
| Worktree branch | `phase1/reproduction` |
| Upstream paper baseline commit (`git merge-base HEAD upstream/main`) | `e71e900000ccc543b4b3f1e57dcf5ddc83425f60` |

## Required Paths

| Path | Status |
| --- | --- |
| `scripts/ReservoirSplatting.py` | Exists |
| `Source/RenderPasses/ReservoirSplatting` | Exists |

## Submodule Revisions

Captured with `git submodule status --recursive`.

| Submodule | Revision | Description |
| --- | --- | --- |
| `external/args` | `a48e1f880813b367d2354963a58dedbf2b708584` | `6.2.2-36-ga48e1f8` |
| `external/fmt` | `a0b8a92e3d1532361c2f7feb63babc5c18d00ef2` | `10.0.0` |
| `external/glfw` | `45ce5ddd197d5c58f50fdd3296a5131c894e5527` | `3.3.7` |
| `external/imgui` | `aceab9a877de0258d19d29a5d87a51b63a8999bf` | `v1.62-3708-gaceab9a87` |
| `external/pybind11` | `7071735dbfc4be70dfb1b6bc312cd09f54e32c62` | `v2.9.2-1-g7071735d` |
| `external/vulkan-headers` | `6ea9413be28455ab172af63d14927f8453cb25f1` | `v1.3.238-18-g6ea9413` |

## Setup Status

| Step | Status |
| --- | --- |
| `setup.sh` | PASS after commit `b2de3ad` permanently changed `tools/packman/packman` from mode `100644` to `100755`, with `XDG_CACHE_HOME="$PWD/.cache"` and externally approved network access |
| CMake preset listing | PASS: `cmake --list-presets` and `cmake --list-presets=build` |
| CMake configure | PASS with `XDG_CACHE_HOME="$PWD/.cache" tools/.packman/cmake/bin/cmake --preset linux-gcc` |
| Build | PASS with `XDG_CACHE_HOME="$PWD/.cache" tools/.packman/cmake/bin/cmake --build --preset linux-gcc-release -j 2` after the Linux portability fixes recorded below |

## Runtime Status

| Check | Status |
| --- | --- |
| Mogwai launch | PASS: created an RTX 5070 Ti Vulkan device and displayed the UI |
| Cornell Box load | PASS: rendered `media/test_scenes/cornell_box.pyscene` |
| No temporal reuse | PASS |
| GatherOnly + Robust | PASS |
| ScatterOnly | PASS |
| ScatterBackup | PASS |
| MultiSplatting with non-zero shutter speed | PASS |
| Camera record/replay | PASS: wrote and replayed `recordings/replay.txt` |
| FrameDumper capture | PASS: wrote 64 PAM frames under `frame-dump/` |

## Issues

- The user installed `vulkan-tools`, and outside-sandbox `vulkaninfo --summary` identified an RTX 5070 Ti with NVIDIA driver `595.58.03`.
- GPU device nodes remain unavailable inside the sandbox. The sandbox probe `/usr/bin/vulkaninfo --summary` fails with `vkCreateInstance failed with ERROR_INCOMPATIBLE_DRIVER`.
- Upstream tracks `tools/packman/packman` as mode `100644`, so the first `bash setup.sh` attempt stopped with `setup.sh: line 26: ./tools/packman/packman: Permission denied`.
- After the local diagnostic workaround `chmod +x tools/packman/packman`, `bash setup.sh` reached Packman but stopped before dependency download: `mkdir: cannot create directory '/home/yu/.cache/packman': Read-only file system`. CMake preset listing and configure were skipped.
- With the additional writable local cache workaround `XDG_CACHE_HOME="$PWD/.cache" bash setup.sh`, Packman created `.cache/packman` and attempted `Fetching python@3.10.5-1-linux-x86_64.tar.gz from bootstrap.packman.nvidia.com ...`, then emitted `Failed to fetch dependencies!`. No lower-level transport error was printed or logged. CMake preset listing and configure were skipped.
- The controller reran `XDG_CACHE_HOME="$PWD/.cache" bash setup.sh` outside the sandbox with network approval. Setup completed, including VS Code workspace setup and the NVTT package patch.
- `cmake --list-presets` and `cmake --list-presets=build` completed successfully. `cmake --preset linux-gcc` detected GCC `15.2.1`, then stopped during its Packman dependency refresh: `mkdir: cannot create directory '/home/yu/.cache/packman': Read-only file system`. CMake reported `execute_process failed command indexes: 1: "Child return code: 1"` and `Configuring incomplete, errors occurred!`.
- With the local cache workaround `XDG_CACHE_HOME="$PWD/.cache" cmake --preset linux-gcc`, Packman dependency refresh completed without a network error. Configure then stopped at `external/pybind11/CMakeLists.txt:8`: `Compatibility with CMake < 3.5 has been removed from CMake.` CMake suggested adding `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` to try configuring anyway.
- The system CMake `4.3.1` incompatibility is resolved by using the author-provided Packman toolchain: `XDG_CACHE_HOME="$PWD/.cache" tools/.packman/cmake/bin/cmake --preset linux-gcc`. Packman CMake `3.24.1` and Ninja `1.10.2` configured successfully and generated `build/linux-gcc`.
- `XDG_CACHE_HOME="$PWD/.cache" tools/.packman/cmake/bin/cmake --build --preset linux-gcc-release -j 2` stopped at Ninja step `[4/874]`, before compiler or linker work. The generated `deploy_dependencies-Release` step invoked `build_scripts/deploycommon.sh` directly and `/bin/sh` reported `/home/yu/storage_pool/NTU/1142/class/icg/term_project/project/.worktrees/phase1-reproduction/build_scripts/deploycommon.sh: Permission denied`. No source fix or file-mode workaround was attempted.
- Commit `a81e2b2` permanently changed `build_scripts/deploycommon.sh` and `build_scripts/wrap_setpath.sh` from mode `100644` to `100755`. The build retry passed dependency deployment, compiled and linked `bin/Release/libFalcor.so`, and continued through several importer and render-pass plugins.
- The retry then stopped at Ninja step `[545/873]` while compiling `Source/RenderPasses/FrameDumper/FrameDumper.cpp`. The first actionable compiler error is `Source/RenderPasses/FrameDumper/FrameDumper.cpp:137:9: error: 'sprintf_s' was not declared in this scope; did you mean 'sprintf'?`. GCC also reports the same undeclared `sprintf_s` call at line `151` and an undeclared `fprintf_s` call at line `156`. No source fix was attempted.
- Commit `83db0e5` replaced the FrameDumper secure-CRT calls with portable `std::snprintf()` and `std::fprintf()` calls. The build then completed successfully and deployed `build/linux-gcc/bin/Release/Mogwai` and `build/linux-gcc/bin/Release/plugins/ReservoirSplatting.so`.
- The first `Scene Settings -> User Interaction -> Recording -> Change Output Directory` attempt threw `Unimplemented` from `Source/Falcor/Core/Platform/Linux/Linux.cpp:350` because upstream Linux Falcor did not implement `chooseFolderDialog()`.
- The committed Linux platform fix implements `chooseFolderDialog()` with a GTK folder chooser. After rebuilding and restarting Mogwai, camera recording/replay and FrameDumper capture both passed.
