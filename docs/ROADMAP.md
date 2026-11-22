# Roadmap / known issues

## Hardware-verified baseline (2026-11-22)

- Target: **original RG35XX**, GarlicOS 1.4.9, TF1 left unchanged; J2ME runtime, launcher scripts and user-provided ROMs on FAT32 TF2.
- Emulator: pinned FreeJ2ME-Plus 1.53, ARM32 uClibc libretro core with RGB565 video conversion; separate ARMHF Zulu Java 8 and private glibc.
- Paired Java + native `0xFD` MIDlet shutdown protocol returns to GarlicOS from tested in-game Exit menus; `load_dummy_on_core_shutdown = "false"` is TF2-only.
- Automatic per-JAR core options and correct image proportions work using `video_dingux_ipu_keep_aspect = "true"` in per-game launcher configs, without globally disabling overrides.
- RMS/in-game progress persisted through a full reboot for **Bounce and Diamond Rush**. This is **not** libretro savestate support.
- One shared Universal Launcher `dispatch.sh` works with generated GarlicOS PORTS shortcuts. An additive-only installer adds new JARs without rewriting tested files ([PR #10](https://github.com/Randoookami/rg35xx-freej2me/pull/10), merged).
- Six user-supplied JAR entries launched with tested virtual phone sizes: Bounce 128×128; Diamond Rush 176×208; Bounce Tales 240×320; Tower Bloxx 240×320; The Sims Bowling **360×360**; James Camerons Avatar 240×320 (**photo demo only**). Sims 360×360 persists after relaunch and full console reboot.
- The additive generator's latest **8/8** Python unit tests passed on the developer's WSL host. No project-wide CI workflow is present. No downloadable end-user release is validated.
- **Sound Off / Backlight Disabled** remains the tested default; reported performance is subjective, not benchmarked.

## Next priorities

1. **Audio / MIDI — open [#3](https://github.com/Randoookami/rg35xx-freej2me/issues/3).** Reproduce the recorded `Manager.retrieveAvailableSynthIndex` / `MIDIPlayer` / Nokia Sound error, inspect soundfont/synthesizer and Java/native output paths, and test isolated opt-in audio configurations. Preserve the silent baseline and avoid game-specific emulator patches.
2. **Gamepad / phone keypad mapping.** Validate D-pad, 0–9, *, #, left/right soft keys and hotkeys; keep per-game remaps separate from core options.
3. **Performance and reliability.** Measure actual new game frames, audio overhead, input latency, CPU/memory use, extended runs and FAT32 integrity; do not mistake frontend refresh rate for game FPS.
4. **Safe update of installed game profiles — [#11](https://github.com/Randoookami/rg35xx-freej2me/issues/11).** Existing no-overwrite additive installer only adds new entries. Determine the active `.opt` file precedence, then design backup-first targeted updates and rollback without touching current working TF2 settings.
5. **GarlicOS Recent behavior — open [#5](https://github.com/Randoookami/rg35xx-freej2me/issues/5).** `X` does not remove J2ME items from Recent; unsupported libretro savestates are separate from working RMS saves.
6. **Reproducible packaging and CI.** Keep source revision pinned; automate offline Python host tests; review third-party licenses and provenance before distributing any JDK/glibc/core/JAR binaries. Keep games, private saves and vendor assets out of Git.
7. **Wider compatibility tests.** A successful launch is not proof of full gameplay or save compatibility. Do not infer a game's resolution merely from its filename; prefer validated declarative profile overrides.

## Development safety

- Do not patch FreeJ2ME C/Java for each individual game when a profile suffices.
- Preserve the tested core/JAR pair, shared dispatcher, RMS saves and TF1. Test changes using isolated TF2-only paths and host-only staging directories.
- **Never reapply the 16-file PR #10 additive install onto existing destinations.** It intentionally refuses overwriting installed entries. The existing Sims profile works at 360×360 and persists after reboot.
- Archived experiment documents preserve early FAIL and untested stages as development history; treat later dated hardware outcomes and this roadmap as the current status.
