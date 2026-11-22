# Add new J2ME games without replacing Universal Launcher v1

**Status:** candidate JAR filenames are known from the user's TF2 directory, but this additive generator has **not yet been verified with WSL tests or on RG35XX hardware**. Keep existing Bounce and Diamond Rush installs intact.

## Six JARs currently on TF2

The user listed these legally supplied local JAR filenames (the game binaries are **not** in the repository):

| Filename | Current status | Profile |
| --- | --- | --- |
| `Bounce.jar` | Tested in Universal Launcher v1 | 128×128, sound Off |
| `Diamond Rush.jar` | Tested in Universal Launcher v1 | 176×208, sound Off |
| `Bounce Tales.jar` | **NEW, untested** | Temporary fallback 240×320, sound Off |
| `Tower Bloxx.jar` | **NEW, untested** | Temporary fallback 240×320, sound Off |
| `The Sims Bowling.jar` | **NEW, untested** | Temporary fallback 240×320, sound Off |
| `James Camerons Avatar.jar` | **NEW, untested** | Temporary fallback 240×320, sound Off |

The four new defaults are guesses for compatibility **only**, not detected resolutions. The universal `video_dingux_ipu_keep_aspect = "true"` option still preserves the selected virtual phone aspect ratio. Change a new game's size later through a safely regenerated additive profile after identifying what that game expects; never modify FreeJ2ME C/Java per title as the first response.

## Architecture and safety

`scripts/stage-additional-jars.py` reuses the hardware-tested `scripts/stage-universal-launcher.py` data validation, fallback ID generator, and `.opt/.cfg` layout. It reads a TF2-mounted directory in WSL **only to list JAR filenames**.

It creates `4 × 4 = 16` **new** files for the four candidates:

- `J2ME/universal-v1/options/<auto-id>.opt`
- `J2ME/universal-v1/launcher-config/<auto-id>.cfg`
- `J2ME/universal-v1/config/FreeJ2ME-Plus/<game-stem>.opt`
- `Roms/PORTS/J2ME_<auto_id>.sh`

The auto IDs include a short hash of the filename, ensuring stable, low-collision names; this produces longer PORTS entry labels than a handcrafted launcher. The stage contains no `dispatch.sh`, no existing game `.opt/.cfg` or shortcuts, no private JARs, and no Java binaries. It writes a separate **host-only** `.host-only/install-plan.json` with file SHA-256 hashes.

The PowerShell copier `scripts/install-additional-jars.ps1` defaults to **dry-run**. With `-Apply` it refuses existing target paths, verifies source/destination hashes, and checks known working TF2 files before copying. It cannot replace the dispatcher, TF1 RetroArch configuration or game saves.

## Step 1: stage in WSL (NO SD writes)

With TF2 connected as Windows `F:` and automatically visible in WSL as `/mnt/f`:

```bash
PUB="$HOME/rg35xx-freej2me-public"
git -C "$PUB" fetch origin
git -C "$PUB" switch --track origin/experiment/additive-jars-01

test -d /mnt/f/Roms/JAVA || { echo "TF2 not visible at /mnt/f/Roms/JAVA"; exit 1; }

python3 -m unittest discover -s "$PUB/tests" -p 'test_additional_jars.py' -v
python3 "$PUB/scripts/stage-additional-jars.py" \
  "$PUB/out/additional-jars-01" --rom-dir /mnt/f/Roms/JAVA
find "$PUB/out/additional-jars-01/Roms/PORTS" -type f -name '*.sh' -exec sh -n {} \;
```

Expected: **7/7 host unit tests** pass, `ADDITIVE_STAGE_OK`, `NEW_GAMES: 4`, `FILES: 16`. Those results are expectations until actually executed on the user's WSL.

To stage **just one game** instead, choose another new, nonexistent output directory and add `--only "Bounce Tales.jar"` to the generator command. Repeat `--only` for selected names. This does not require editing the program.

## Step 2: inspect copier in Windows PowerShell (dry-run first)

```powershell
$PUB = '\\wsl.localhost\Ubuntu-24.04\home\nikch\rg35xx-freej2me-public'
$ps = Join-Path $PUB 'scripts\install-additional-jars.ps1'
$stage = Join-Path $PUB 'out\additional-jars-01'

# This mode reads source and TF2, but writes NOTHING:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ps -Stage $stage -Tf2Root 'F:\'
```

Require `PREFLIGHT_OK` and `DRY_RUN_OK`. If TF2 is another drive letter, **do not use F:\**. Inspect the detected new filenames and ensure the earlier Universal Launcher worked on that card. Before a write, run `chkdsk F:` (without `/f`) to check FAT32 if the card was previously corrupted. Exit any Windows file manager writing to the SD before the actual copy.

```powershell
# Run ONLY after dry-run succeeds and drive identity is checked:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ps -Stage $stage -Tf2Root 'F:\' -Apply
```

Require `ADDITIVE_COPY_OK` before safely ejecting the card. If a source/hash/destination check fails, STOP; do not delete or overwrite the existing data to force success. Partial additions from a failed copy should be reviewed before retrying.

## Step 3: actual RG35XX tests

Start with **Bounce Tales** and proceed to Tower Bloxx, The Sims Bowling, and Avatar only after identifying the first game's behavior. Check that a newly generated PORTS entry launches, whether the display is cropped or padded, sound stays off, gameplay accepts button input, and whether in-game Exit returns directly to GarlicOS. Some games may request different resolution or missing Java APIs. Record the observed outcome rather than assuming the fallback works.

Finally, re-launch the existing `J2ME_bounce` and `J2ME_diamond_rush` entries as regression checks. Neither should have changed.

Logs are written by the unchanged dispatcher to `/mnt/SDCARD/J2ME/logs/universal-<auto-id>.log`. Reports or logs may be shared without proprietary JARs or RMS save files.

## Rollback

The host-only install plan names precisely the added 16 files. The copier does not edit or delete anything. In the event of failure, do **not** remove `J2ME/universal-v1` as a whole: it also contains the two known working games and the common dispatcher. Any subsequent removal must target only new files listed in the additive install plan, after confirming they are no longer needed. Never alter TF1, `J2ME/test-saves`, the paired emulator JAR, core, or runtime.
