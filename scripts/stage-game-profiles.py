#!/usr/bin/env python3
"""Stage independent, declarative J2ME game profiles for the original RG35XX.

No SD card is modified. Uses the already hardware-tested exit core+Java pairing.
First hardware test of automatic core-option loading and aspect correction only.
"""
import json
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEVICE = "/mnt/SDCARD"
TEST_PREFIX = DEVICE + "/J2ME/profile-test-01"
RA = "/mnt/mmc/CFW/retroarch/retroarch"
CORE = DEVICE + "/J2ME/core/freej2me_plus_exit_test_libretro.so"
SYSTEM = DEVICE + "/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin"
SAVE = DEVICE + "/J2ME/test-saves"
MANIFEST = ROOT / "profiles" / "games.json"
RESOLUTIONS = {
    "128x128", "176x208", "120x160", "128x160", "132x176",
    "176x220", "208x208", "220x220", "240x320", "320x240",
}


def quote_config(value):
    if "\n" in value or "\r" in value or '"' in value:
        raise ValueError("Invalid configuration value")
    return '"' + value + '"'


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/stage-game-profiles.py /path/to/NEW/staging-dir")
    dest = Path(sys.argv[1]).expanduser().resolve()
    if dest.exists():
        raise SystemExit("ABORT: destination already exists, no overwrites: " + str(dest))
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if doc.get("schema_version") != 1:
        raise SystemExit("ABORT: unsupported game profile schema")
    games = doc.get("games", [])
    if not isinstance(games, list) or not games:
        raise SystemExit("ABORT: empty profile list")
    seen = set()
    plans = []

    # Validate everything before creating any output.
    for game in games:
        ident = game["id"]
        name = game["display_name"]
        rom = game["rom_file"]
        resolution = game["resolution"]
        sound = game["sound"]
        backlight = game["backlight"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", ident) or ident in seen:
            raise SystemExit("ABORT: invalid or repeated game ID")
        seen.add(ident)
        if not re.fullmatch(r"[A-Za-z0-9 _().-]+\.jar", rom) or "/" in rom or "\\" in rom:
            raise SystemExit("ABORT: unsafe ROM filename: " + rom)
        if not re.fullmatch(r"[A-Za-z0-9 _().-]+", name):
            raise SystemExit("ABORT: invalid game display name: " + name)
        if resolution not in RESOLUTIONS or sound not in ("off", "on"):
            raise SystemExit("ABORT: invalid resolution/sound profile: " + ident)
        if backlight not in ("Disabled", "Green", "Cyan", "Orange", "Violet", "Red"):
            raise SystemExit("ABORT: invalid backlight profile: " + ident)
        plans.append((ident, name, rom, resolution, sound, backlight))

    out = dest / "J2ME" / "profile-test-01"
    port = dest / "Roms" / "PORTS"
    (out / "config" / "FreeJ2ME-Plus").mkdir(parents=True)
    (out / "options").mkdir(parents=True)
    (out / "launcher-config").mkdir(parents=True)
    port.mkdir(parents=True)

    for ident, name, rom, resolution, sound, backlight in plans:
        opts = "\n".join((
            "freej2me_resolution = " + quote_config(resolution),
            "freej2me_sound = " + quote_config(sound),
            "freej2me_backlightcolor = " + quote_config(backlight),
            "",
        ))
        # Two compatible loading paths for older versions of RetroArch.
        # Core-options-path is preferred; game-specific .opt is a fallback.
        (out / "options" / (ident + ".opt")).write_text(opts, encoding="ascii")
        (out / "config" / "FreeJ2ME-Plus" / (Path(rom).stem + ".opt")).write_text(
            opts, encoding="ascii"
        )

        cfgpath = TEST_PREFIX + "/launcher-config/" + ident + ".cfg"
        lines = [
            "# Experimental, TF2-only. No changes to TF1/global configuration.",
            "system_directory = " + quote_config(DEVICE + "/J2ME/test-system"),
            "savefile_directory = " + quote_config(SAVE),
            "savestate_directory = " + quote_config(SAVE),
            "config_save_on_exit = " + quote_config("false"),
            "load_dummy_on_core_shutdown = " + quote_config("false"),
            "core_options_path = " + quote_config(TEST_PREFIX + "/options/" + ident + ".opt"),
            "rgui_config_directory = " + quote_config(TEST_PREFIX + "/config"),
            "game_specific_options = " + quote_config("true"),
            "video_force_aspect = " + quote_config("true"),
            "video_aspect_ratio_auto = " + quote_config("true"),
            "video_scale_integer = " + quote_config("false"),
            "history_list_enable = " + quote_config("false"),
        ]
        (out / "launcher-config" / (ident + ".cfg")).write_text(
            "\n".join(lines) + "\n", encoding="ascii"
        )

        launcher = port / ("J2ME_" + ident.replace("-", "_") + "_Profile_Test.sh")
        rompath = DEVICE + "/Roms/JAVA/" + rom
        logpath = DEVICE + "/J2ME/logs/profile-test-" + ident + ".log"
        body = "\n".join((
            "#!/bin/sh",
            "# Independently staged J2ME profile test. No global config writes.",
            "RA=" + shlex.quote(RA),
            "CORE=" + shlex.quote(CORE),
            "CFG=" + shlex.quote(cfgpath),
            "ROM=" + shlex.quote(rompath),
            "SYSTEM=" + shlex.quote(SYSTEM),
            "LOG=" + shlex.quote(logpath),
            "mkdir -p /mnt/SDCARD/J2ME/logs /mnt/SDCARD/J2ME/test-saves",
            "{",
            "  echo '=== J2ME PROFILE TEST ==='",
            "  echo 'PROFILE=" + ident + " RESOLUTION=" + resolution + "'",
            '  for file in "$RA" "$CORE" "$CFG" "$ROM" "$SYSTEM/java" "$SYSTEM/freej2me_plus-lr.jar"; do',
            '    if [ ! -f "$file" ]; then echo "MISSING: $file"; sync; exit 1; fi',
            "  done",
            '  export HOME=/mnt/mmc/CFW/retroarch',
            '  "$RA" -v --appendconfig "$CFG" -L "$CORE" "$ROM"',
            "  RC=$?",
            '  echo "RETROARCH_EXIT_CODE=$RC"',
            "} > \"$LOG\" 2>&1",
            "sync",
            "exit 0",
            "",
        ))
        launcher.write_text(body, encoding="ascii")
        launcher.chmod(0o755)
        print("STAGED:", ident, "=>", resolution, sound, backlight)

    print("PROFILE_STAGE_OK:", dest)
    print("Next: inspect each game's Core Options menu and observed picture before deploying more broadly.")
    for p in sorted(dest.rglob("*")):
        if p.is_file():
            print(" ", p.relative_to(dest))


if __name__ == "__main__":
    main()
