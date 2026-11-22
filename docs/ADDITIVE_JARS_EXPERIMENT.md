# Add new J2ME games without replacing Universal Launcher v1

**Status:** WSL host checks passed (7/7 unit tests and shell syntax), PowerShell syntax and dry-run checks passed, and the four new JAR shortcuts were tried on original RG35XX hardware. Bounce Tales and Tower Bloxx run almost perfectly with fallback defaults; Avatar JAR is a working photo demo, not the anticipated playable game; The Sims Bowling also runs well after the user experimentally selected 360×360. All four can exit to GarlicOS. Keep existing Bounce and Diamond Rush installs intact.

## Six JARs currently on TF2

The user listed these legally supplied local JAR filenames (the game binaries are **not** in the repository):

| Filename | Current status | Profile |
| --- | --- | --- |
| `Bounce.jar` | Tested in Universal Launcher v1 | 128×128, sound Off |
| `Diamond Rush.jar` | Tested in Universal Launcher v1 | 176×208, sound Off |
| `Bounce Tales.jar` | **NEW, untested** | Temporary fallback 240×320, sound Off |
| `Tower Bloxx.jar` | **NEW, untested** | Temporary fallback 240×320, sound Off |
| `The Sims Bowling.jar` | **Hardware tested** | **360×360** (user-verified), sound Off |
| `James Camerons Avatar.jar` | **NEW, untested** | Temporary fallback 240×320, sound Off |

The four new defaults are guesses for compatibility **only**, not detected resolutions. The universal `video_dingux_ipu_keep_aspect = "true"` option still preserves the selected virtual phone aspect ratio. Change a new game's size later through a safely regenerated additive profile after identifying what that game expects; never modify FreeJ2ME C/Java per title as the first response.

## Additive-JAR first hardware feedback (2026-11-22)

**Observed by user on original RG35XX, not inferred from JAR filenames:**

| JAR | Startup / rendering | Exit to GarlicOS | Current interpretation |
| --- | --- | --- | --- |
| `Bounce Tales.jar` | Works almost perfectly out of the box | PASS | Promising at fallback `240x320`; precise compatibility still needs a longer test |
| `Tower Bloxx.jar` | Works almost perfectly out of the box | PASS | Promising at fallback `240x320`; precise compatibility still needs a longer test |
| `The Sims Bowling.jar` | Runs well after experimentally selecting **360×360** | PASS | Verified virtual phone resolution for this JAR edition; 240×320 fallback was incorrect |
| `James Camerons Avatar.jar` | Launches, but is a **photo demo**, not the expected playable Avatar game | PASS | Correctly classify this particular JAR as a photo demo, not as game compatibility evidence |

**Resolution precision:** the first batch used **240×320 portrait** for all four new JARs. The user then tested The Sims Bowling and confirmed **360×360 square** was correct for their particular edition. The other three used 240×320, including the Avatar *photo demo* (not a playable Avatar game). No game-specific Java or RGB565 changes were needed.

**Next gate before merging PR:** retry known `J2ME_bounce` and `J2ME_diamond_rush` entries as regression tests, confirm no saves changed unexpectedly, and document the Sims screen condition. Preserve the original four new `.opt/.cfg` files until a controlled, backed-up per-profile update workflow is available. No global TF1 changes, no per-game emulator patches.

## Declarative corrections for previously discovered games

`profiles/additional-overrides.json` records `The Sims Bowling.jar` with `resolution: 360x360`. The new `stage-additional-jars.py` version applies this override after filename discovery and **before** generating `.opt` files. The hash-derived profile ID is unchanged: `auto-the-sims-bowling-c00b0e66`. All other new JARs retain the conservative fallback. This is a per-variant data fix, not a hardcoded game branch in the emulator.

**Important deployment rule:** the existing `out/additional-jars-01` stage was generated before the correction and still contains 240×320 for Sims; **do not repeat the 16-file copy or overwrite the known working TF2 files**. Updated staging requires a brand-new WSL output directory, and the existing no-overwrite copier must correctly reject attempts to replace the already installed files. The verified 360×360 setting may currently have been selected in RetroArch's menu; persistence across a completely fresh relaunch is not yet separately confirmed. A narrowly scoped, backup-first *profile-update* workflow will be a later improvement.

To validate new output without touching TF2:

```bash
PUB="$HOME/rg35xx-freej2me-public"
git -C "$PUB" pull --ff-only
python3 -m unittest discover -s "$PUB/tests" -p 'test_additional_jars.py' -v
# To regenerate, supply the same six-name dummy directory used previously,
# but a NEW output destination:
python3 "$PUB/scripts/stage-additional-jars.py" \
  "$PUB/out/additional-jars-after-sims-01" \
  --rom-dir "$ROM_NAMES_ONLY"
```

The last command requires that `ROM_NAMES_ONLY` still points to the host-only six-name directory; otherwise recreate it. It only proves generation. **Do not copy these 16 files** onto the already installed TF2.

## Architecture and safety

`scripts/stage-additional-jars.py` reuses the hardware-tested `scripts/stage-universal-launcher.py` data validation, fallback ID generator, and `.opt/.cfg` layout. It reads a TF2-mounted directory in WSL **only to list JAR filenames**.

It creates `4 × 4 = 16` **new** files for the four candidates:

- `J2ME/universal-v1/options/<auto-id>.opt`
- `J2ME/universal-v1/launcher-config/<auto-id>.cfg`
- `J2ME/universal-v1/config/FreeJ2ME-Plus/<game-stem>.opt`
- `Roms/PORTS/J2ME_<auto_id>.sh`

The auto IDs include a short hash of the filename, ensuring stable, low-collision names; this produces longer PORTS entry labels than a handcrafted launcher. The stage contains no `dispatch.sh`, no existing game `.opt/.cfg` or shortcuts, no private JARs, and no Java binaries. It writes a separate **host-only** `.host-only/install-plan.json` with file SHA-256 hashes.

The PowerShell copier `scripts/install-additional-jars.ps1` defaults to **dry-run**. With `-Apply` it refuses existing target paths, verifies source/destination hashes, and checks known working TF2 files before copying. It cannot replace the dispatcher, TF1 RetroArch configuration or game saves.

## WSL note: if TF2 is not mounted at /mnt/f

On 2026-11-22, the first user command run stopped at `test -d /mnt/f/Roms/JAVA` (no `=== UNIT TESTS ===` line followed); therefore **none of the seven new unit tests nor the additive generator had yet run**. Windows can see a removable `F:` drive even if WSL's `/mnt/f` is not mounted.

**No need to mount or write to TF2 just to test the host generator.** It scans *only filenames* and checks the two existing known names; create harmless empty filename placeholders on WSL's own home filesystem using the user's six reported names:

```bash
PUB="$HOME/rg35xx-freej2me-public"
git -C "$PUB" pull --ff-only
ROM_NAMES_ONLY="$(mktemp -d "$HOME/j2me-romnames-XXXXXX")"
touch "$ROM_NAMES_ONLY/Bounce.jar" \
  "$ROM_NAMES_ONLY/Diamond Rush.jar" \
  "$ROM_NAMES_ONLY/Bounce Tales.jar" \
  "$ROM_NAMES_ONLY/Tower Bloxx.jar" \
  "$ROM_NAMES_ONLY/The Sims Bowling.jar" \
  "$ROM_NAMES_ONLY/James Camerons Avatar.jar"
python3 -m unittest discover -s "$PUB/tests" -p 'test_additional_jars.py' -v
python3 "$PUB/scripts/stage-additional-jars.py" \
  "$PUB/out/additional-jars-01" --rom-dir "$ROM_NAMES_ONLY"
find "$PUB/out/additional-jars-01/Roms/PORTS" -type f -name '*.sh' -exec sh -n {} \;
```

The `ROM_NAMES_ONLY` files are **zero-byte dummy filename entries on WSL only**, never proprietary game JARs and never copied to TF2. Staging still produces only the 16 real config/shortcut files; the original six JARs stay on TF2. The install copier separately confirms **every new JAR really exists at `F:\Roms\JAVA`** before allowing an actual copy.

Do not use `--Apply` until source generation, dry-run, and actual TF2 JAR existence checks all pass.

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
