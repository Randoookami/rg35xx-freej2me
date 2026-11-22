# FreeJ2ME-Plus on the original RG35XX

An **experimental community port** of [FreeJ2ME-Plus](https://github.com/TASEmulators/freej2me-plus) for the **original Anbernic RG35XX** running **GarlicOS 1.4.9** (not RG35XX Plus/H/2024 or GarlicOS 2.x).

This project is **unofficial** and is not affiliated with the upstream emulator authors, Anbernic, or GarlicOS.

> **Status: working proof of concept, not yet a plug-and-play release.** Two J2ME games have reached playable gameplay on actual hardware. Sound is currently disabled, and several integration problems remain.

## Verified on hardware

| Component | Verified configuration |
| --- | --- |
| Device | Original Anbernic RG35XX, ARMv7 Cortex-A9 |
| OS | Stock GarlicOS 1.4.9; Linux 3.10.37 |
| Emulator | FreeJ2ME-Plus 1.53, upstream commit `52b25f75824d247c23e352625be45157bfe87620` |
| Libretro core | ARM32 EABI5 soft-float/uClibc, output converted to RGB565 |
| Java process | Azul Zulu OpenJDK 8u512, ARM hard-float, with separate Debian 11 glibc 2.31 |
| Storage | TF1: untouched GarlicOS; TF2: FAT32, runtime, scripts, game files, logs and saves |
| Bounce | Playable; observed phone resolution **128×128** |
| Diamond Rush | Playable intro; observed phone resolution **176×208** |

Both games were tested with **Virtual Phone Sound: Off** and **LCD Backlight Color: Off**. These resolutions describe the tested JAR versions, not every release of each game. FPS has **not** been objectively benchmarked.

## How it works

```text
GarlicOS 1.4.9 / RetroArch (TF1; not modified)
    |
    +-- FreeJ2ME-Plus libretro core (ARM32/uClibc, RGB565; TF2)
           |
           +-- Java wrapper + FreeJ2ME-Plus libretro JAR (TF2)
                   |
                   +-- Zulu Java 8 ARMHF + private glibc loader (TF2)
                           |
                           +-- user-supplied J2ME game .jar
```

## Known limitations

- **Audio is off** for current successful tests. A MIDI-path exception was observed with sound enabled, alongside failed gameplay progression in Bounce.
- **Exiting from a game's own menu** does not currently terminate the libretro session. Exit through RetroArch until the lifecycle issue is fixed.
- **Aspect ratio and scaling** are not automated; the current view can stretch portrait games across a 4:3 display.
- **Gamepad mapping**, saves across restarts, and performance tuning need further validation.
- **TF2 FAT32 integrity** should be monitored: filesystem corruption was encountered during development; its cause has not been established.
- No supported installer or tested downloadable release bundle is available yet.

## Source, builds, and installation

- [Build notes](docs/BUILD.md) — source pin and native cross-build recipe.
- [Hardware architecture](docs/ARCHITECTURE.md) — how two ABIs and two C libraries coexist.
- [Compatibility report](docs/COMPATIBILITY.md) — observed game results.
- [Known issues and roadmap](docs/ROADMAP.md).
- [Third-party software and redistribution](docs/THIRD_PARTY.md).

This repository tracks **RG35XX-specific patches and integration materials** rather than copying an entire upstream checkout. Get the unmodified emulator from the [upstream repository](https://github.com/TASEmulators/freej2me-plus) at the pinned commit.

**No commercial J2ME game JARs, proprietary assets, user saves, or third-party JDK/glibc binary bundles are included.** Provide legally obtained game files yourself.

## Credits and license

FreeJ2ME-Plus originated with David Richardson (Recompile) and collaborators, and is maintained by the [TAS Emulators / FreeJ2ME-Plus project](https://github.com/TASEmulators/freej2me-plus). This port builds on their work. Upstream FreeJ2ME code is **GPL-3.0-or-later**; see [LICENSE](LICENSE) for the upstream copyright, ObjectWeb ASM notice, and GPL terms. See [third-party notes](docs/THIRD_PARTY.md) before distributing binaries.

The RGB565 adaptation and launch integration are community port modifications; they are not changes already present upstream.
