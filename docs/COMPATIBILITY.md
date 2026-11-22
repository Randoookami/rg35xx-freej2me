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

## Visual caveats

The tested 176×208 Diamond Rush content initially showed blank right/bottom regions at incorrect phone resolutions. Selecting 176×208 filled the virtual game area. Physical display aspect-ratio correction is unfinished and the game may still appear stretched to 4:3.

## Sound caveat

With sound enabled, a Java exception was observed in `javax.microedition.media.Manager.retrieveAvailableSynthIndex` / `MIDIPlayer.start` / `com.nokia.mid.sound.Sound.play`. In Bounce, turning virtual sound off coincided with restoring successful gameplay. This is evidence of an audio-path problem, **not yet a proven single root cause for every game**.

## How to contribute results

Provide: device revision and GarlicOS version, emulator/core revision, game edition (without uploading proprietary game files), phone resolution, sound/backlight options, whether input and progression work, approximate performance (clearly labeled estimate vs measurement), and sanitized logs.
