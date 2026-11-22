# Universal J2ME Launcher, experiment 01

**Status: host-only prototype, not tested on original RG35XX hardware. Do not merge or replace the existing working launchers.**

## Goal

Replace hand-maintained per-game program logic with **one shared POSIX-sh dispatcher**, plus a declarative profile for each game. GarlicOS's existing PORTS menu still needs visible entries, so the host generator creates very short, automatically generated `.sh` *shortcuts*, not manually programmed game launchers.

This stage **does not** implement an on-device graphical chooser. A single clickable multi-game chooser would require a compatible on-screen UI, which we have not established for stock GarlicOS 1.4.9. Avoid assuming an interactive terminal is available in PORTS.

## Architecture

```text
profiles/games.json                         (known game configuration)
              + optional host ROM scan        (unknown JAR filenames only)
                    |
                    v
scripts/stage-universal-launcher.py         (runs in WSL, NOT on RG35XX)
                    |
                    v
out/universal-launcher-01/                  (host-only, no SD writes)
  J2ME/universal-v1/dispatch.sh             <-- ONE shared runtime dispatcher
  J2ME/universal-v1/options/{game-id}.opt   <-- FreeJ2ME core options
  J2ME/universal-v1/launcher-config/{game-id}.cfg
  J2ME/universal-v1/config/FreeJ2ME-Plus/{game-stem}.opt
  J2ME/universal-v1/staged-profiles.json
  Roms/PORTS/J2ME_{id}.sh                   <-- auto-generated one-line shortcut
```

The shared dispatcher accepts a validated profile ID and a JAR path, checks that the required files exist, and invokes the **already verified** launcher command:

```sh
/mnt/mmc/CFW/retroarch/retroarch -v --appendconfig "<game.cfg>" \
    -L /mnt/SDCARD/J2ME/core/freej2me_plus_exit_test_libretro.so "<game.jar>"
```

On the target device, the dispatcher uses only `/bin/sh` and standard utilities. **No Python, jq, Java rebuild, native compile, or extra UI dependency is needed on the RG35XX**.

Existing tested paths are retained: `J2ME/test-system` for the paired Java frontend and `J2ME/test-saves` for RMS saves. Do not remove or overwrite either one.

## How it chooses settings

The generator reads `profiles/games.json`:

| Tested JAR edition | Resolution | Sound | Backlight |
| --- | --- | --- | --- |
| Bounce.jar | 128×128 | Off | Disabled |
| Diamond Rush.jar | 176×208 | Off | Disabled |

Profiles use the verified GarlicOS option `video_dingux_ipu_keep_aspect = "true"`, as well as the working `load_dummy_on_core_shutdown = "false"` option. The game selection changes only the profile, not the emulator code.

If you optionally scan a mounted ROM directory on **the WSL host**, unknown JAR filenames generate **automatic fallback profiles**: 240×320, Sound Off, Backlight Disabled. This is *not* resolution detection, JAR compatibility validation, or manifest-derived device compatibility. If a game needs another phone size, add an explicit profile in `profiles/games.json`. Filenames with unusual characters are currently skipped rather than executing unsafe shell expansions.

## Stage on WSL — zero SD writes

```bash
PUB="$HOME/rg35xx-freej2me-public"
git -C "$PUB" fetch origin
git -C "$PUB" switch --track origin/experiment/universal-launcher-01

# Unit tests: no attached TF1 or TF2 required.
python3 -m unittest discover -s "$PUB/tests" \
  -p 'test_universal_launcher.py' -v

# Known games only; creates a NEW directory on the Linux filesystem:
python3 "$PUB/scripts/stage-universal-launcher.py" \
  "$PUB/out/universal-launcher-01"

# Check every generated launcher and shared dispatcher syntax:
find "$PUB/out/universal-launcher-01" -name '*.sh' -type f -exec sh -n {} \;

find "$PUB/out/universal-launcher-01" -type f | sort
```

Expected final marker: `UNIVERSAL_STAGE_OK`. The generator intentionally refuses to overwrite an existing staging destination, and rejects direct staging to a WSL-mounted removable or Windows drive.

**Optional, only if TF2 is visible in WSL under `/mnt/f`** and has the expected `Roms/JAVA` directory:

```bash
python3 "$PUB/scripts/stage-universal-launcher.py" \
  "$PUB/out/universal-launcher-scan-01" \
  --rom-dir /mnt/f/Roms/JAVA
```

This `--rom-dir` argument is **read only**. It enumerates JAR filenames, does not parse proprietary game data, copy ROMs, or alter the card. It requires the two known JAR files to be present and aborts otherwise, to prevent broken known-game shortcuts. If Windows assigns another drive letter, adjust only that optional scan path.

## Hardware acceptance criteria — NOT YET PERFORMED

When WSL tests pass, stage the generated files on TF2 *under their own paths* without overwriting the existing test launches. Then check:

1. Bounce and Diamond Rush launch through `J2ME_bounce` and `J2ME_diamond_rush` with their correct automatic 128×128 and 176×208 profiles.
2. Both keep the correct square/portrait aspect immediately, and can exit directly to GarlicOS.
3. Repeat launches preserve pre-existing RMS game progress and do not change the global TF1 RetroArch configuration.
4. A new JAR produces an auto-generated shortcut and a conservative fallback profile, with its actual compatibility explicitly unverified.
5. If a JAR is missing, the dispatcher logs a precise `MISSING:` diagnostic and exits instead of trying to run Java.
6. The existing known-good exit-test and profile-test PORTS entries remain untouched.

## Limits and rollback

- No built-in on-device graphical JAR picker yet; PORTS shortcuts are generated automatically in bulk.
- The 240×320 fallback does not prove the correct resolution for unknown MIDlets. No automatic MANIFEST.MF-based sizing inference is claimed.
- For profile edits, regenerate to a **new** staging destination. The first version does not overwrite installed files; controlled update/backup tooling can be developed once a hardware-tested baseline exists.
- Do not copy or distribute commercial JARs, private Java/glibc binaries, SD saves or logs to GitHub.
- Rollback: launch previous working `J2ME_Bounce_Exit_Test`, `J2ME_DiamondRush_Exit_Test`, or known profile-test launchers; they remain separate. After copying elsewhere, remove *only* `J2ME/universal-v1` and its generated `Roms/PORTS/J2ME_{id}.sh` shortcuts if needed; never remove `J2ME/test-saves`.
