# Experimental J2ME game profiles, stage 01

**Status: game-option switching PASSED on hardware; aspect still requires an automatic-launch test. Draft, not merged.**

## Problem and approach

FreeJ2ME-Plus 1.53 reads `freej2me_resolution`, `freej2me_sound` and `freej2me_backlightcolor` as **libretro core options**. Resolution is read at `retro_init` and passed to the Java process before the game starts. A RetroArch `--appendconfig` file alone should **not** be assumed to set these values.

The native FreeJ2ME core already sends `RETRO_ENVIRONMENT_SET_GEOMETRY` with `Geometry.aspect_ratio = width / height` whenever the actual framebuffer changes. Test RetroArch's *Core Provided* aspect mode first; do not alter the RGB565 converter.

[Official Libretro documentation](https://docs.libretro.com/guides/overrides/) distinguishes `.opt` files for core options from `.cfg` files for frontend settings. Some RetroArch releases have also differed in the handling of `core_options_path`; this must be established on GarlicOS 1.4.9 hardware rather than presumed.

This experiment makes **declarative game definitions**, not game-specific emulator modifications:

| Game variant | Virtual phone | Sound | Backlight |
| --- | --- | --- | --- |
| Bounce | 128×128 | Off | Disabled |
| Diamond Rush | 176×208 | Off | Disabled |

## Follow-up hardware feedback: manual Keep Aspect Ratio fixes both games

On 2026-11-22 the tester confirmed **Keep Aspect Ratio was Off** in the running experimental RetroArch session, and switching it **On** corrected the visible shape in **both Bounce and Diamond Rush**. This isolates the aspect failure to the RetroArch frontend setting and rules out a need to change the Java virtual resolution or the RGB565 converter for the two test games.

**Why the original config was not enough:** the generated `--appendconfig` already contains `video_force_aspect = "true"`, yet the visible menu reported Off. A late-loaded RetroArch override is one plausible explanation; however, the exact precedence on the GarlicOS build has not yet been diagnosed. RetroArch can load core/game overrides after other config files. Do not mistake this hypothesis for a verified cause.

### Stage-02 controlled diagnostic — prevent auto-loading overrides

Without modifying stage-01 launchers or any tested core/JAR, stage a **second, separate** pair of PORTS launchers:

```bash
PUB="$HOME/rg35xx-freej2me-public"
git -C "$PUB" pull --ff-only
python3 -m py_compile "$PUB/scripts/stage-aspect-02.py"
python3 "$PUB/scripts/stage-aspect-02.py"
find "$PUB/out/game-profiles-aspect-02" -type f -print | sort
```

`scripts/stage-aspect-02.py` requires the successful stage-01 folder at `out/game-profiles-01`, refuses to overwrite anything, and stages exactly **four files**:

```text
J2ME/profile-test-02/launcher-config/bounce.cfg
J2ME/profile-test-02/launcher-config/diamond-rush.cfg
Roms/PORTS/J2ME_bounce_Aspect_Test.sh
Roms/PORTS/J2ME_diamond_rush_Aspect_Test.sh
```

The configs preserve the successful stage-01 core-option file paths and the `video_force_aspect = "true"` setting. The **only new RetroArch config variable** is:

```ini
auto_overrides_enable = "false"
```

This variable is applied *only in the test launch configuration* to see if an auto-loaded core/game override was resetting Keep Aspect Ratio. It does not alter TF1's configuration and preserves separate `J2ME/test-saves`. All stage-01 launchers continue to exist.

**Acceptance test:** launch Bounce Aspect Test with no manual settings changes; check `Settings → Video → Scaling → Keep Aspect Ratio` is **On** on startup and the image is square. Repeat with Diamond Rush. If still Off, do not save settings; report both results, and inspect actual runtime override/config file precedence before trying another change. New logs: `J2ME/logs/profile-aspect-02-bounce.log`, `profile-aspect-02-diamond-rush.log`.

**Note:** `auto_overrides_enable = "false"` is diagnostic. If it has broader effects (e.g. disables a user's custom mapping), keep it out of the final shipping configuration and implement a narrowly scoped override solution instead.

## Generate a temporary TF2 overlay

```bash
PUB="$HOME/rg35xx-freej2me-public"
git -C "$PUB" fetch origin
git -C "$PUB" switch --track origin/experiment/game-profiles-01

python3 -m py_compile "$PUB/scripts/stage-game-profiles.py"
python3 "$PUB/scripts/stage-game-profiles.py" "$PUB/out/game-profiles-01"

find "$PUB/out/game-profiles-01" -type f -print | sort
```

Generated files under the staging directory:

- `J2ME/profile-test-01/options/{bounce,diamond-rush}.opt` — explicit core-options files
- `J2ME/profile-test-01/config/FreeJ2ME-Plus/{Bounce,Diamond Rush}.opt` — content-specific option lookup on RetroArch versions that prefer per-game `.opt`
- `J2ME/profile-test-01/launcher-config/{bounce,diamond-rush}.cfg` — per-launch append configs, video aspect auto and no global config save
- `Roms/PORTS/J2ME_bounce_Profile_Test.sh` and `J2ME_diamond_rush_Profile_Test.sh` — standalone test entries

The generator never writes to TF1/TF2. It refuses to overwrite an existing staging directory. Only the **existing**, already hardware-tested experimental exit core and Java JAR on TF2 are referenced; no new native code or JAR build is required.

Copy *only* the generated files to matching TF2 relative paths, after verifying the SD mount and inspecting the files. Do not replace the existing `J2ME_Bounce_Exit_Test.sh`, `J2ME_DiamondRush_Exit_Test.sh`, the tested core, Java JAR, or game saves.

## First hardware feedback (2026-11-22)

User tested generated profile launchers on original RG35XX/GarlicOS 1.4.9:

| Check | Report |
| --- | --- |
| Bounce automatically selects 128×128 | **PASS** |
| Diamond Rush automatically selects 176×208 | **PASS** |
| Switching back to Bounce selects 128×128 again | **PASS** |
| Display preserves original aspect | **FAIL**: stretched display persists |

**Interpretation:** per-launch FreeJ2ME core-option files load correctly, including on a subsequent game switch; the aspect-ratio configuration is not yet sufficient. Do **not** patch Java or RGB565 rendering on this evidence alone. The native code already emits geometry with width/height, but GarlicOS's RetroArch frontend may enforce 4:3, or overrides may take precedence.

### Next targeted hardware diagnostic (no SD writes)

1. Start `J2ME_bounce_Profile_Test` and observe stretched image.
2. Open RetroArch's menu, then **Settings → Video → Scaling → Keep Aspect Ratio**. Record if the option is currently **Off** or **On**. GarlicOS 1.4.9 commonly exposes this simple toggle rather than the modern Aspect Ratio list.
3. If **Off**, turn **On** *temporarily* and resume gameplay. Does Bounce become square, with black bars? If already **On**, note that and **do not toggle it off**.
4. Do not choose Save Configuration, Save Core Override, Save Game Override, or change any TF1 files.
5. Exit the game normally. Report toggle status and observed result; only then decide whether to correct the launcher config or diagnose frontend override precedence.

This is a **diagnostic**, not a confirmed fix. Do not assume modern RetroArch's numeric `aspect_ratio_index` constants: versions differ.

## What to check on hardware

1. Launch **Bounce Profile Test**. Under Quick Menu → Core Options, check `Phone Resolution = 128x128`, `Virtual Phone Sound = Off`, `LCD Backlight Color = Disabled`. Do not correct these manually before recording observed values.
2. Observe Bounce's picture: on a 640×480 RG35XX screen, a 1:1 square should take **480×480** pixels and show approximately **80-pixel black bars left and right**, if fullscreen aspect correction is active.
3. Exit from within Bounce. Launch **Diamond Rush Profile Test** and check that the phone resolution switched **automatically** to `176x208` and sound remained Off.
4. With correct aspect, Diamond Rush should render at approximately **406×480** pixels, with side bars about **117 pixels** wide.
5. Exit Diamond Rush; launch Bounce again, confirm `128×128` returned automatically. Confirm existing RMS progress survives.
6. If the screen is still stretched, open Settings → Video → Scaling to inspect the **actual** Aspect Ratio selection. Do not save any global changes. Report whether there is a `Core Provided` choice.
7. If the resolution remains wrong, inspect the Quick Menu's `Active Options File` (if shown) and send the two profile-test logs from `/mnt/SDCARD/J2ME/logs/`.

The aspect bar widths are predictions, not device measurements. The RetroArch numeric `aspect_ratio_index` differs across versions, so this first experiment intentionally does **not** hardcode one. We will add a confirmed per-launch override once the GarlicOS version's aspect selection behavior is measured.

## Why this design preserves the known-good baseline

- New launchers and config files have isolated paths on TF2.
- `config_save_on_exit = "false"` prevents normal frontend-wide config saves; some core-option file writes may still occur in test-only TF2 paths.
- `rgui_config_directory` points to a dedicated test config directory on TF2, not global TF1 config.
- The working RGB565 core, exit protocol, Java process and RMS save directory are unchanged.
- This proof of concept is **not** yet an installer, and automatic profile loading is **not** claimed until tested on GarlicOS.

## Rollback

Launch the previous `J2ME_Bounce_Exit_Test` and `J2ME_DiamondRush_Exit_Test` entries, which remain untouched. The staged `J2ME/profile-test-01` and `Roms/PORTS/*_Profile_Test.sh` files can later be removed separately, after logs are preserved. Do not delete `J2ME/test-saves` or any global RetroArch files.
