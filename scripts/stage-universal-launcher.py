#!/usr/bin/env python3
"""Stage one shared RG35XX J2ME dispatcher and data-driven game shortcuts.

Runs on the developer's host (WSL Python 3), never on the RG35XX.
Output is a new isolated folder, NEVER an SD card. No emulator build required.
"""
import argparse
import hashlib
import json
import re
import shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARD = "/mnt/SDCARD"
BASE = CARD + "/J2ME/universal-v1"
ROMS = CARD + "/Roms/JAVA"
CORE = CARD + "/J2ME/core/freej2me_plus_exit_test_libretro.so"
JAVA_BIN = CARD + "/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin"
RA = "/mnt/mmc/CFW/retroarch/retroarch"
PROFILE_FILE = ROOT / "profiles" / "games.json"
DEFAULTS = {"resolution": "240x320", "sound": "off", "backlight": "Disabled"}
# Actual upstream FreeJ2ME-Plus 1.53 supported core-option values.
RESOLUTIONS = {
    "96x65", "101x64", "101x80", "128x128", "130x130", "120x160",
    "128x160", "160x128", "132x176", "208x173", "176x208", "176x220",
    "220x176", "208x208", "220x220", "180x320", "320x180", "240x240",
    "240x260", "208x320", "320x240", "240x400", "400x240", "320x320",
    "240x432", "240x480", "360x360", "352x416", "480x320", "360x480",
    "480x360", "360x640", "640x360", "480x640", "640x480", "345x800",
    "800x345", "480x800", "800x480", "480x854", "854x480", "240x320",
}
BACKLIGHT = {"Disabled", "Green", "Cyan", "Orange", "Violet", "Red"}
# First implementation intentionally handles predictable FAT32-safe names.
SAFE_JAR = re.compile(r"[A-Za-z0-9 _().+-]+\.jar", re.I)
SAFE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def quoted(value):
    if any(c in value for c in ('"', "\r", "\n", "\\")):
        raise ValueError("invalid .cfg value")
    return '"' + value + '"'


def slug(value):
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (text[:36].rstrip("-") or "game")


def validate_game(game):
    ident = game["id"]
    rom = game["rom_file"]
    if not isinstance(ident, str) or not SAFE_ID.fullmatch(ident):
        raise ValueError("invalid game id: " + repr(ident))
    if not isinstance(rom, str) or not SAFE_JAR.fullmatch(rom):
        raise ValueError("unsafe/non-ASCII ROM filename: " + repr(rom))
    if game["resolution"] not in RESOLUTIONS:
        raise ValueError("unsupported resolution for " + ident)
    if game["sound"] not in ("on", "off"):
        raise ValueError("invalid sound option for " + ident)
    if game["backlight"] not in BACKLIGHT:
        raise ValueError("invalid backlight option for " + ident)
    if not isinstance(game["display_name"], str) or not game["display_name"].strip():
        raise ValueError("game without display name: " + ident)


def read_profiles():
    source = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    if source.get("schema_version") != 1:
        raise ValueError("unsupported game manifest schema")
    games = source.get("games")
    if not isinstance(games, list) or not games:
        raise ValueError("empty game manifest")
    ids, names = set(), set()
    for game in games:
        validate_game(game)
        if game["id"] in ids or game["rom_file"].casefold() in names:
            raise ValueError("duplicate game id or JAR")
        ids.add(game["id"])
        names.add(game["rom_file"].casefold())
    return games


def discover(games, rom_dir):
    """Add unknown ROM filenames with safe defaults; do NOT guess screen sizes."""
    if rom_dir is None:
        return games
    if not rom_dir.is_dir():
        raise ValueError("ROM read-only directory is missing: " + str(rom_dir))
    seen = {g["rom_file"].casefold() for g in games}
    ids = {g["id"] for g in games}
    files = sorted((p for p in rom_dir.iterdir()
                    if p.is_file() and not p.is_symlink()
                    and p.suffix.casefold() == ".jar"),
                   key=lambda p: p.name.casefold())
    if len(files) > 200:
        raise ValueError("too many JAR files in one directory (>200)")
    actual = {p.name.casefold() for p in files}
    missing = sorted(g["rom_file"] for g in games if g["rom_file"].casefold() not in actual)
    if missing:
        raise ValueError("known JAR missing from supplied ROM directory: " + ", ".join(missing))
    for jar in files:
        if jar.name.casefold() in seen:
            continue
        if not SAFE_JAR.fullmatch(jar.name):
            print("SKIP UNSAFE FILENAME:", repr(jar.name))
            continue
        suffix = hashlib.sha256(jar.name.encode("utf-8")).hexdigest()[:8]
        ident = "auto-" + slug(jar.stem) + "-" + suffix
        if ident in ids:
            raise ValueError("auto id collision: " + ident)
        game = {
            "id": ident, "display_name": jar.stem, "rom_file": jar.name,
            **DEFAULTS,
        }
        validate_game(game)
        games.append(game)
        seen.add(jar.name.casefold())
        ids.add(ident)
        print("DISCOVERED: " + jar.name + " (fallback 240x320, sound off)")
    return games


DISPATCHER = """#!/bin/sh
# One shared dispatcher for ALL generated J2ME game shortcuts.
# Deliberately POSIX sh: no Python, jq, shell sourcing or game-specific code.
CARD=/mnt/SDCARD
BASE="$CARD/J2ME/universal-v1"
RA=/mnt/mmc/CFW/retroarch/retroarch
CORE="$CARD/J2ME/core/freej2me_plus_exit_test_libretro.so"
JAVA_BIN="$CARD/J2ME/test-system/freej2me_plus_runtime/linux-arm/bin"
ROM_ROOT="$CARD/Roms/JAVA"

ID="$1"
ROM="$2"
case "$ID" in
    ""|*[!a-z0-9-]*) echo "Invalid profile id" >&2; exit 2 ;;
esac
case "$ROM" in
    "$ROM_ROOT"/*.jar) ;;
    *) echo "JAR must be under $ROM_ROOT" >&2; exit 2 ;;
esac
BASENAME=$(basename "$ROM")
case "$BASENAME" in
    ""|*.jar) ;;
    *) echo "Invalid JAR basename" >&2; exit 2 ;;
esac
if [ "$ROM" != "$ROM_ROOT/$BASENAME" ]; then
    echo "Nested paths or traversal are unsupported" >&2
    exit 2
fi

CFG="$BASE/launcher-config/$ID.cfg"
OPT="$BASE/options/$ID.opt"
LOGDIR="$CARD/J2ME/logs"
mkdir -p "$LOGDIR" || exit 3
LOG="$LOGDIR/universal-$ID.log"
{
    echo "=== RG35XX UNIVERSAL J2ME LAUNCHER ==="
    echo "PROFILE=$ID"
    echo "ROM=$ROM"
    for F in "$RA" "$CORE" "$JAVA_BIN/java" "$JAVA_BIN/freej2me_plus-lr.jar" "$CFG" "$OPT" "$ROM"; do
        if [ ! -f "$F" ]; then
            echo "MISSING: $F"
            exit 3
        fi
    done
    export HOME=/mnt/mmc/CFW/retroarch
    "$RA" -v --appendconfig "$CFG" -L "$CORE" "$ROM"
    RC=$?
    echo "RETROARCH_EXIT_CODE=$RC"
    sync
    exit "$RC"
} > "$LOG" 2>&1
"""


def make_config(game):
    ident = game["id"]
    opts = (
        "freej2me_resolution = " + quoted(game["resolution"]) + "\n"
        "freej2me_sound = " + quoted(game["sound"]) + "\n"
        "freej2me_backlightcolor = " + quoted(game["backlight"]) + "\n"
    )
    settings = [
        "# TF2-only. Settings validated in Bounce and Diamond Rush experiments.",
        "system_directory = " + quoted(CARD + "/J2ME/test-system"),
        "savefile_directory = " + quoted(CARD + "/J2ME/test-saves"),
        "savestate_directory = " + quoted(CARD + "/J2ME/test-saves"),
        'config_save_on_exit = "false"',
        'load_dummy_on_core_shutdown = "false"',
        "core_options_path = " + quoted(BASE + "/options/" + ident + ".opt"),
        "rgui_config_directory = " + quoted(BASE + "/config"),
        'game_specific_options = "true"',
        'video_force_aspect = "true"',
        'video_dingux_ipu_keep_aspect = "true"',
        'video_aspect_ratio_auto = "true"',
        'video_scale_integer = "false"',
        'history_list_enable = "false"',
    ]
    return opts, "\n".join(settings) + "\n"


def stage(destination, games):
    if destination.exists():
        raise ValueError("ABORT: destination exists; refusal to overwrite: " + str(destination))
    # Validate all resulting paths and avoid case-insensitive FAT32 collisions.
    filenames = set()
    stems = set()
    for game in games:
        validate_game(game)
        fname = "J2ME_" + game["id"].replace("-", "_") + ".sh"
        if fname.casefold() in filenames:
            raise ValueError("conflicting PORTS filenames")
        filenames.add(fname.casefold())
        if game["rom_file"].rsplit(".", 1)[0].casefold() in stems:
            raise ValueError("conflicting content option file stems")
        stems.add(game["rom_file"].rsplit(".", 1)[0].casefold())
    base = destination / "J2ME" / "universal-v1"
    ports = destination / "Roms" / "PORTS"
    for folder in ("options", "launcher-config", "config/FreeJ2ME-Plus"):
        (base / folder).mkdir(parents=True, exist_ok=True)
    ports.mkdir(parents=True)

    shared = base / "dispatch.sh"
    shared.write_text(DISPATCHER, encoding="ascii")
    shared.chmod(0o755)
    for game in games:
        ident = game["id"]
        options, cfg = make_config(game)
        (base / "options" / (ident + ".opt")).write_text(options, encoding="ascii")
        (base / "launcher-config" / (ident + ".cfg")).write_text(cfg, encoding="ascii")
        (base / "config" / "FreeJ2ME-Plus" /
         (game["rom_file"].rsplit(".", 1)[0] + ".opt")).write_text(
            options, encoding="ascii")
        launcher = ports / ("J2ME_" + ident.replace("-", "_") + ".sh")
        rom_path = ROMS + "/" + game["rom_file"]
        launcher.write_text(
            "#!/bin/sh\n"
            "# Generated entry; all runtime logic lives in one dispatcher.\n"
            "exec /bin/sh " + shlex.quote(BASE + "/dispatch.sh") + " "
            + shlex.quote(ident) + " " + shlex.quote(rom_path) + "\n",
            encoding="ascii",
        )
        launcher.chmod(0o755)
        print("PROFILE:", ident, game["rom_file"], game["resolution"],
              game["sound"], game["backlight"])
    (base / "staged-profiles.json").write_text(
        json.dumps({"schema_version": 1, "games": games}, indent=2,
                   ensure_ascii=True) + "\n", encoding="ascii")
    print("UNIVERSAL_STAGE_OK:", destination)
    for item in sorted(destination.rglob("*")):
        if item.is_file():
            print(" ", item.relative_to(destination))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="NEW host-only staging directory")
    parser.add_argument(
        "--rom-dir", type=Path, default=None,
        help="optional read-only host path to TF2 Roms/JAVA; discover unknown JARs",
    )
    args = parser.parse_args()
    try:
        games = discover(read_profiles(), args.rom_dir)
        stage(args.destination.expanduser().resolve(), games)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, "ERROR: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
