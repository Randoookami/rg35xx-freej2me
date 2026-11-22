# Tested games / compatibility

These are **observations on one original RG35XX**, not performance guarantees or redistribution permissions. Different editions of a game may require different settings.

| Game | Result | Tested FreeJ2ME phone resolution | Notes |
| --- | --- | --- | --- |
| Bounce (Nokia J2ME) | Playable; first level completed | 128×128 | Sound Off. Normal colors after disabling simulated LCD backlight. |
| Diamond Rush | Playable; introductory level completed | 176×208 | Sound Off. Subjectively some input lag and approximately 20–25 FPS, **not instrument-measured**. |

Shared device setup: GarlicOS 1.4.9, FreeJ2ME-Plus 1.53 native ARM32 core with RGB565 conversion, Zulu Java 8u512 ARMHF, private glibc 2.31 on TF2.

## Visual caveats

The tested 176×208 Diamond Rush content initially showed blank right/bottom regions at incorrect phone resolutions. Selecting 176×208 filled the virtual game area. Physical display aspect-ratio correction is unfinished and the game may still appear stretched to 4:3.

## Sound caveat

With sound enabled, a Java exception was observed in `javax.microedition.media.Manager.retrieveAvailableSynthIndex` / `MIDIPlayer.start` / `com.nokia.mid.sound.Sound.play`. In Bounce, turning virtual sound off coincided with restoring successful gameplay. This is evidence of an audio-path problem, **not yet a proven single root cause for every game**.

## How to contribute results

Provide: device revision and GarlicOS version, emulator/core revision, game edition (without uploading proprietary game files), phone resolution, sound/backlight options, whether input and progression work, approximate performance (clearly labeled estimate vs measurement), and sanitized logs.
