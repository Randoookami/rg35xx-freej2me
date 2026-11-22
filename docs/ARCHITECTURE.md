# Architecture: original RG35XX / GarlicOS 1.4.9

> **Current integration status (2026-11-22):** the TF2-only Universal Launcher, per-game core options, Dingux/IPU aspect preservation and paired Java/native MIDlet shutdown are verified on hardware. This document includes historical early-stage system paths and uncertainties; see [ROADMAP.md](ROADMAP.md) and [COMPATIBILITY.md](COMPATIBILITY.md) for the latest scope.

## Device facts from real hardware diagnostics

- Linux 3.10.37, ARMv7, four Cortex-A9 cores, VFPv3/NEON.
- Reported memory total: 237,624 KiB; no swap.
- TF1's FAT partition is mounted at `/mnt/mmc`.
- TF2's FAT32 partition is mounted at `/mnt/SDCARD` and was mounted without `noexec` during testing.
- The existing firmware already uses loop devices and supports ext4; neither was needed for the first playable games.

## Process boundary matters

```
RetroArch (GarlicOS system, uClibc)
  -> freej2me_plus_rgb565_libretro.so (ARM EABI5, soft-float, linked to libc.so.0)
       -> fork/exec a shell wrapper
            -> Zulu OpenJDK 8u512 (ARMHF, glibc 2.31 in a private TF2 directory)
                 -> FreeJ2ME-Plus 1.53 libretro Java JAR
                      -> user-provided MIDlet (.jar)
```

The **native libretro core** and the **Java executable** are separate processes, so the former can use the GarlicOS uClibc ABI and the latter ARM hard-float glibc ABI. This does **not** make the two C libraries interchangeable within one process.

The original Java executable requested `/lib/ld-linux-armhf.so.3`, absent from GarlicOS. The successful device test used a **copy of Java** whose ELF interpreter was changed with `patchelf` to:

```
/mnt/SDCARD/J2ME/runtime/glibc/lib/ld-linux-armhf.so.3
```

A launcher set `LD_LIBRARY_PATH` to the private ARMHF glibc libraries and JRE libraries. The original Zulu JDK archive was kept unmodified in the build workspace.

## Video

Upstream FreeJ2ME 1.53 outputs `RETRO_PIXEL_FORMAT_XRGB8888`, with a 32-bit pixel buffer. On tested GarlicOS 1.4.9, frames appeared as regular colored stripes. The RG35XX patch advertises `RETRO_PIXEL_FORMAT_RGB565`, converts each pixel from XRGB8888 to RGB565 and passes `width * 2` as pitch. This was observed to fix severe corruption in the two tested games.

**Video format and game resolution are separate settings.** A game-specific resolution is selected via FreeJ2ME core options. **Aspect-ratio preservation was subsequently resolved on the original RG35XX** with TF2-only `video_dingux_ipu_keep_aspect = "true"` in each launcher `.cfg`; see [GAME_PROFILES_EXPERIMENT.md](GAME_PROFILES_EXPERIMENT.md).

## TF1 / TF2 separation

TF1 retains unmodified GarlicOS. TF2 holds libretro core, Java wrapper, patched Java executable, extracted glibc, the FreeJ2ME libretro JAR, legal game files, logs and saves.

For the tested setup the wrapper and JAR lived at:
```
/mnt/SDCARD/BIOS/freej2me_plus_runtime/linux-arm/bin/java
/mnt/SDCARD/BIOS/freej2me_plus_runtime/linux-arm/bin/freej2me_plus-lr.jar
```

The actual Java runtime was under `/mnt/SDCARD/J2ME/runtime/java8/jre`; the separate glibc under `/mnt/SDCARD/J2ME/runtime/glibc`.

TF2 was FAT32. During staging, `cp -aL` dereferenced JRE symlinks into regular files before copying to FAT32. The native launcher on TF2 is a shell script, not a copy of the stock binary.

## Why this is still experimental

The stand-alone Java `-version` and Java2D headless tests passed on physical hardware. Six JAR entries now launch at their observed resolutions, with the Avatar-named entry confirmed as a **photo demo**, not the playable game. Safe in-game exit, automatic scaling and RMS save persistence were verified in the initial two games; Sims Bowling's 360×360 also survives reboot. **Audio, keypad mappings, sustained performance, wider save compatibility and an end-user release remain unverified.**

Current Universal Launcher paths (TF2) are `/mnt/SDCARD/J2ME/universal-v1/dispatch.sh`, `options/<game-id>.opt`, `launcher-config/<game-id>.cfg` and `/mnt/SDCARD/Roms/PORTS/J2ME_<id>.sh`. The tested paired core/JAR reside under `J2ME/core/` and `J2ME/test-system/`. Earlier `BIOS/` paths above are part of the historical setup, **not** the current launcher layout.
