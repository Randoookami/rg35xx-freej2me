# Roadmap / known issues

## Baseline (observed working)

- Original RG35XX, GarlicOS 1.4.9, all J2ME-specific runtime files on TF2.
- RGB565 rendering patch in the libretro core.
- Bounce at 128×128; Diamond Rush at 176×208.
- Virtual Phone Sound off; LCD Backlight Color off.

## Next priorities

1. **MIDlet lifecycle — verified in two games:** the 0xFD Java-to-native signaling plus TF2-only `load_dummy_on_core_shutdown = "false"` returns from either game's Exit menu directly to GarlicOS. Manual Quit RetroArch still works. Broader game and unexpected-crash coverage remain future work.
2. **Independent game profiles + Universal Launcher — hardware PASS in two games:** generated per-JAR `.opt` files apply Bounce 128×128 and Diamond Rush 176×208; one shared POSIX dispatcher and automatically generated GarlicOS PORTS shortcuts launch both on real hardware. Next: a third legally owned JAR, fallback profile validation, and maintainable profile installation without replacing stable files.
3. **Aspect ratio and scaling — verified in two games:** `video_dingux_ipu_keep_aspect = "true"` in the TF2-only launcher `.cfg` preserves both square and portrait images automatically, without disabling global overrides. More games/display modes remain to be tested.
4. **Input remapping:** sensible RG35XX button-to-phone keypad defaults plus per-game overrides.
5. **Audio/MIDI:** diagnose exception and support optional stable sound; keep silent mode for baseline.
6. **Measure actual FPS and latency:** distinguish new game frames from RetroArch's reported refresh.
7. **Save persistence and resilience:** in-game progress survived clean exit and full reboot for Bounce and Diamond Rush. Continue checking FAT32 integrity and additional games.
8. **GarlicOS Recent and save states:** FreeJ2ME 1.53 has no libretro serialization; GarlicOS 1.4.9 displays the expected unsupported-savestate warning in Recent. Investigate why X does not remove these history entries and support safe history cleanup independently from the emulator. Do not pretend RMS saves are savestates.
9. **Reproducible packaging:** verified scripts, license review, TF2-only installer instructions, integrity hashes, then optional releases.

## Safety and scope

Do not optimize per game by modifying the VM. Prefer shared adapters, core fixes or declarative profiles. Preserve the known-good RGB565 build and original FreeJ2ME source commit as a regression reference.
