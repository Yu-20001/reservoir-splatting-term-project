# Reservoir Splatting Host Environment

Capture date: 2026-06-01

## Operating System

Command: `cat /etc/os-release`

Exit status: `0`

```text
NAME="Arch Linux"
PRETTY_NAME="Arch Linux"
ID=arch
BUILD_ID=rolling
ANSI_COLOR="38;2;23;147;209"
HOME_URL="https://archlinux.org/"
DOCUMENTATION_URL="https://wiki.archlinux.org/"
SUPPORT_URL="https://bbs.archlinux.org/"
BUG_REPORT_URL="https://gitlab.archlinux.org/groups/archlinux/-/issues"
PRIVACY_POLICY_URL="https://terms.archlinux.org/docs/privacy-policy/"
LOGO=archlinux-logo
```

## Kernel

Command: `uname -srmo`

Exit status: `0`

```text
Linux 6.18.21-1-lts x86_64 GNU/Linux
```

## NVIDIA GPU Sandbox Observation

Command: `nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader`

Exit status: `9`

```text
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver. Make sure that the latest NVIDIA driver is installed and running.
```

## NVIDIA GPU Host Verification

The controller ran the same command outside the sandbox.

Command: `nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader`

Exit status: `0`

```text
NVIDIA GeForce RTX 5070 Ti, 595.58.03, 16303 MiB
```

## NVIDIA Device Nodes Inside Sandbox

Command: `ls -l /dev/nvidia*`

Exit status: `2`

```text
ls: cannot access '/dev/nvidia*': No such file or directory
```

## PCI GPU Enumeration Inside Sandbox

Command: `lspci -nnk | rg -i -A3 'vga|3d|display|nvidia'`

Exit status: `0`

Relevant NVIDIA excerpt

```text
01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GB203 [GeForce RTX 5070 Ti] [10de:2c05] (rev a1)
	Subsystem: Gigabyte Technology Co., Ltd Device [1458:4180]
	Kernel driver in use: nvidia
	Kernel modules: nouveau, nvidia_drm, nvidia
01:00.1 Audio device [0403]: NVIDIA Corporation GB203 High Definition Audio Controller [10de:22e9] (rev a1)
	Subsystem: NVIDIA Corporation Device [10de:0000]
	Kernel driver in use: snd_hda_intel
	Kernel modules: snd_hda_intel
```

## GPU Visibility Notes

**Observations**

- Inside the sandbox, `nvidia-smi` is installed and runs, but exits with status `9` because it cannot communicate with the NVIDIA driver.
- Outside the sandbox, controller verification reports `NVIDIA GeForce RTX 5070 Ti, 595.58.03, 16303 MiB`.
- Inside the sandbox, PCI enumeration sees an NVIDIA GeForce RTX 5070 Ti and reports `Kernel driver in use: nvidia`.
- Required NVIDIA device nodes are absent inside the sandbox.
- Inside the sandbox, the earlier `vulkaninfo --summary` probe reported `not installed`.
- Outside the sandbox, controller verification confirms that Vulkan host verification passes for the NVIDIA GeForce RTX 5070 Ti.

**Inference**

- The absent NVIDIA device nodes are consistent with the sandboxed `nvidia-smi` communication failure.

## Vulkan Sandbox Observation

Command: `vulkaninfo --summary`

Status: `not installed`

Exit status: `127`

## Vulkan Host Verification

The controller ran `vulkaninfo --summary` outside the sandbox after the user installed `vulkan-tools`.

Status: `passed`

```text
Vulkan Instance Version = 1.4.341
deviceType = PHYSICAL_DEVICE_TYPE_DISCRETE_GPU
deviceName = NVIDIA GeForce RTX 5070 Ti
driverName = NVIDIA
driverInfo = 595.58.03
```

## CMake

Command: `cmake --version`

Exit status: `0`

```text
cmake version 4.3.1

CMake suite maintained and supported by Kitware (kitware.com/cmake).
```

## Ninja

Command: `ninja --version`

Exit status: `0`

```text
1.13.2
```

## Python

Command: `python --version`

Exit status: `0`

```text
Python 3.14.4
```

## FFmpeg

Command: `ffmpeg -version`

Exit status: `0`

```text
ffmpeg version n8.1 Copyright (c) 2000-2026 the FFmpeg developers
```
