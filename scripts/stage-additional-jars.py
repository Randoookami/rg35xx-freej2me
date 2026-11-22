#!/usr/bin/env python3
"""Stage ONLY NEW FreeJ2ME JAR shortcuts and profiles for an installed Universal Launcher.

Runs in WSL/Python 3 on the host. Reads JAR filenames, never writes to TF1/TF2.
Uses the same validation, IDs, configuration, and launcher quoting as v1.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_SCRIPT = ROOT / "scripts" / "stage-universal-launcher.py"
PROFILE_OVERRIDES = ROOT / "profiles" / "additional-overrides.json"


def existing_generator():
    spec = importlib.util.spec_from_file_location("j2me_universal_generator", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load tested universal generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_profile_overrides(generator, known_names):
    """Read declarative corrections for specific discovered JAR filename variants."""
    data = json.loads(PROFILE_OVERRIDES.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("profiles"), list):
        raise ValueError("Invalid additional profile overrides schema")
    overrides = {}
    for entry in data["profiles"]:
        if not isinstance(entry, dict):
            raise ValueError("Profile override is not an object")
        extra_keys = set(entry) - {"rom_file", "resolution", "sound", "backlight"}
        if extra_keys:
            raise ValueError("Unexpected profile override keys: " + repr(extra_keys))
        name = entry.get("rom_file")
        if not isinstance(name, str) or not generator.SAFE_JAR.fullmatch(name):
            raise ValueError("Unsafe override JAR filename: " + repr(name))
        key = name.casefold()
        if key in overrides or key in known_names:
            raise ValueError("Duplicate or known-game override: " + name)
        settings = {k: entry[k] for k in ("resolution", "sound", "backlight") if k in entry}
        if not settings:
            raise ValueError("Empty profile override for " + name)
        # Use the same tested core-option value validation as all other profiles.
        probe = {
            "id": "auto-override-check", "display_name": name,
            "rom_file": name, **generator.DEFAULTS, **settings
        }
        generator.validate_game(probe)
        overrides[key] = settings
    return overrides


def stage_additions(destination, rom_dir, selected):
    generator = existing_generator()
    # All validations and discovery run before creating the staging folder.
    if destination.exists():
        raise ValueError("ABORT: destination exists; refusal to overwrite: " + str(destination))
    if re.match(r"^/(?:mnt/(?:[a-zA-Z]|SDCARD|mmc)|media|run/media)(?:/|$)",
                str(destination)):
        raise ValueError("ABORT: destination must be host-only; cannot write a mounted drive")
    if not rom_dir.is_dir():
        raise ValueError("read-only ROM directory not found: " + str(rom_dir))
    known = generator.read_profiles()
    known_names = {g["rom_file"].casefold() for g in known}
    all_games = generator.discover([dict(g) for g in known], rom_dir)
    new_games = [g for g in all_games if g["rom_file"].casefold() not in known_names]
    overrides = read_profile_overrides(generator, known_names)
    if selected:
        wanted = {name.casefold() for name in selected}
        new_names = {g["rom_file"].casefold() for g in new_games}
        missing = wanted - new_names
        if missing:
            raise ValueError("--only must name discoverable NEW JARs: "
                             + ", ".join(sorted(missing)))
        new_games = [g for g in new_games if g["rom_file"].casefold() in wanted]
    if not new_games:
        raise ValueError("No new safe JAR files detected; nothing to stage")

    # Filename-specific hardware feedback overrides the conservative fallback,
    # without changing hash-derived IDs or touching any already-installed files.
    for game in new_games:
        change = overrides.get(game["rom_file"].casefold())
        if change:
            game.update(change)
            generator.validate_game(game)
            print("VERIFIED PROFILE:", game["rom_file"], game["resolution"])

    # The FAT32 destination is case-insensitive. Check all generated path names
    # before producing files. The target SD's actual existing files are checked
    # separately by the PowerShell copy preflight.
    output = []
    for game in new_games:
        generator.validate_game(game)
        ident = game["id"]
        stem = game["rom_file"].rsplit(".", 1)[0]
        output.append((game, [
            "J2ME/universal-v1/options/" + ident + ".opt",
            "J2ME/universal-v1/launcher-config/" + ident + ".cfg",
            "J2ME/universal-v1/config/FreeJ2ME-Plus/" + stem + ".opt",
            "Roms/PORTS/J2ME_" + ident.replace("-", "_") + ".sh",
        ]))
    relative_files = [name for _, names in output for name in names]
    if len({p.casefold() for p in relative_files}) != len(relative_files):
        raise ValueError("Case-insensitive destination path collision")

    destination.mkdir(parents=True)
    written = []
    for game, names in output:
        options, cfg = generator.make_config(game)
        shell = (
            "#!/bin/sh\n"
            "# Auto-generated incremental entry for the already-installed universal dispatcher.\n"
            "exec /bin/sh "
            + shlex.quote(generator.BASE + "/dispatch.sh") + " "
            + shlex.quote(game["id"]) + " "
            + shlex.quote(generator.ROMS + "/" + game["rom_file"]) + "\n"
        )
        for name, text in zip(names, (options, cfg, options, shell)):
            dest = destination / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="ascii")
            if name.endswith(".sh"):
                dest.chmod(0o755)
            written.append({
                "path": name,
                "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
            })
        print("ADD:", game["rom_file"], "ID:", game["id"],
              "fallback", game["resolution"], "sound", game["sound"])

    # This is HOST-ONLY metadata. Do not copy .host-only to the microSD.
    meta = destination / ".host-only"
    meta.mkdir()
    manifest = {
        "schema_version": 1,
        "purpose": "additive-only",
        "required_existing": [
            "J2ME/universal-v1/dispatch.sh",
            "J2ME/universal-v1/options/bounce.opt",
            "J2ME/universal-v1/options/diamond-rush.opt",
            "Roms/PORTS/J2ME_bounce.sh",
            "Roms/PORTS/J2ME_diamond_rush.sh",
        ],
        "games": new_games,
        "files": written,
    }
    (meta / "install-plan.json").write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
        encoding="ascii")
    print("ADDITIVE_STAGE_OK:", destination)
    print("FILES:", len(written), "NEW_GAMES:", len(new_games))
    print("No existing dispatcher, known-game profile, ROM or JAR is included.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path,
                        help="NEW WSL host-only directory for incremental files")
    parser.add_argument("--rom-dir", required=True, type=Path,
                        help="read-only mounted TF2 Roms/JAVA directory")
    parser.add_argument("--only", action="append", default=[], metavar="NAME.jar",
                        help="optional exact additional JAR filename; repeatable")
    args = parser.parse_args()
    try:
        stage_additions(
            args.destination.expanduser().resolve(),
            args.rom_dir.expanduser().resolve(),
            args.only,
        )
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        parser.exit(1, "ERROR: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
