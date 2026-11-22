# Tested games / compatibility

These are **observations on one original RG35XX**, not performance guarantees or redistribution permissions. Different editions of a game may require different settings.

| Game | Result | Tested FreeJ2ME phone resolution | Notes |
| --- | --- | --- | --- |
| Bounce (Nokia J2ME) | Playable; first level completed | 128×128 | Sound Off. Normal colors after disabling simulated LCD backlight. |
| Diamond Rush | Playable; introductory level completed | 176×208 | Sound Off. Subjectively some input lag and approximately 20–25 FPS, **not instrument-measured**. |

Shared device setup: GarlicOS 1.4.9, FreeJ2ME-Plus 1.53 native ARM32 core with RGB565 conversion, Zulu Java 8u512 ARMHF, private glibc 2.31 on TF2.

## Exit and save persistence regression (2026-11-22)

With the experimental paired Java JAR + ARM32 RGB565 core and the test-only RetroArch setting `load_dummy_on_core_shutdown = "false"`:

| Test | Bounce | Diamond Rush |
| --- | --- | --- |
| In-game Exit returns directly to GarlicOS | PASS | PASS |
| Quick Menu → Main Menu → Quit RetroArch | PASS | PASS |
| Re-launch after exit | PASS | PASS |
| In-game progress persists after console reboot | PASS | PASS |
| Existing non-test launcher still runs | PASS | PASS |
| Native RetroArch savestates | Not implemented | Not implemented |

Legacy launchers intentionally still have the original in-game exit limitation. Test reports are based on user-observed hardware behavior. These tests do not prove compatibility with other J2ME games.

## Automatic profiles and aspect test (2026-11-22)

| Check | Bounce | Diamond Rush |
| --- | --- | --- |
| Game profile auto-selects phone resolution | PASS: 128×128 | PASS: 176×208 |
| Switching back to Bounce restores its resolution | PASS | PASS (preceding game) |
| Automatic aspect correction with `video_dingux_ipu_keep_aspect = "true"` | PASS | PASS |
| Correct aspect without diagnostic `auto_overrides_enable = "false"` | PASS | PASS |

The 176×208 Diamond Rush variant initially showed missing screen content with an incorrect phone profile; per-game `.opt` files resolved this. The generic `video_force_aspect = "true"` frontend setting alone did not activate GarlicOS's **Keep Aspect Ratio** control. The Dingux/IPU setting did. This is a user-observed result on the original RG35XX, not proof across other RetroArch versions or JAR editions.

## Additional JARs via additive Universal Launcher (2026-11-22)

These entries were installed as **new files only**; the user tested the resulting shortcuts on the original RG35XX. All four return successfully to the GarlicOS menu.

| User-supplied JAR variant | Launcher observations | Virtual phone profile | In-game exit |
| --- | --- | --- | --- |
| Bounce Tales | Runs almost perfectly out of the box; longer gameplay and saves not measured | Fallback 240×320, Sound Off | PASS |
| Tower Bloxx | Runs almost perfectly out of the box; longer gameplay and saves not measured | Fallback 240×320, Sound Off | PASS |
| The Sims Bowling | Runs correctly; **360×360 persists after full game relaunch and console reboot** | **360×360 confirmed** for this user-supplied JAR variant; Sound Off | PASS |
| James Camerons Avatar | Runs, but this JAR is a **photo demo**, not a playable game | Fallback 240×320, Sound Off | PASS |

The initial fallback was `240×320`; the user then experimentally identified and successfully tested **360×360** for this exact Sims Bowling JAR, including persistence after a full reboot. All six supplied JAR entries subsequently launched with the intended resolutions. This is not a claim of sustained, feature-complete compatibility; the three newer playable games have not completed long-session/save testing. Other editions may need different phone sizes. Do not conflate the photo demo with a playable Avatar JAR.

## Sound caveat

With sound enabled, a Java exception was observed in `javax.microedition.media.Manager.retrieveAvailableSynthIndex` / `MIDIPlayer.start` / `com.nokia.mid.sound.Sound.play`. In Bounce, turning virtual sound off coincided with restoring successful gameplay. This is evidence of an audio-path problem, **not yet a proven single root cause for every game**.

## How to contribute results

Provide: device revision and GarlicOS version, emulator/core revision, game edition (without uploading proprietary game files), phone resolution, sound/backlight options, whether input and progression work, approximate performance (clearly labeled estimate vs measurement), and sanitized logs.
