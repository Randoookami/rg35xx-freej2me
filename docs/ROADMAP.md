# Roadmap / known issues

## Baseline (observed working)

- Original RG35XX, GarlicOS 1.4.9, all J2ME-specific runtime files on TF2.
- RGB565 rendering patch in the libretro core.
- Bounce at 128×128; Diamond Rush at 176×208.
- Virtual Phone Sound off; LCD Backlight Color off.

## Next priorities

1. **MIDlet lifecycle:** quitting through a game's menu leaves the libretro session running. Determine Java-to-native end-of-MIDlet signaling, then request appropriate RetroArch shutdown. Do not force-kill Java as a substitute for clean shutdown.
2. **Independent game profiles:** preserve game resolution and other core options per JAR without changing the user's TF1/RetroArch global configuration.
3. **Aspect ratio and scaling:** avoid stretching portrait and square phone displays into 4:3.
4. **Input remapping:** sensible RG35XX button-to-phone keypad defaults plus per-game overrides.
5. **Audio/MIDI:** diagnose exception and support optional stable sound; keep silent mode for baseline.
6. **Measure actual FPS and latency:** distinguish new game frames from RetroArch's reported refresh.
7. **Save persistence and resilience:** verify after clean shutdown/restart and check FAT32 integrity.
8. **Reproducible packaging:** verified scripts, license review, TF2-only installer instructions, integrity hashes, then optional releases.

## Safety and scope

Do not optimize per game by modifying the VM. Prefer shared adapters, core fixes or declarative profiles. Preserve the known-good RGB565 build and original FreeJ2ME source commit as a regression reference.
