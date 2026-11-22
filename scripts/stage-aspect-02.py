#!/usr/bin/env python3
"""Stage a non-destructive, four-file aspect-override isolation test for TF2.

Requires the successful stage-01 profile files to exist under out/game-profiles-01.
This script never edits the existing stage-01 files, SD cards, cores or JARs.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "out" / "game-profiles-01"
DEST = ROOT / "out" / "game-profiles-aspect-02"
CARD = "/mnt/SDCARD"

GAMES = ("bounce", "diamond-rush")
CFG_REL = "J2ME/profile-test-01/launcher-config/"
PORTS_REL = "Roms/PORTS/"

if not SRC.is_dir():
    raise SystemExit("ABORT: run stage-game-profiles.py and verify stage-01 first.")
if DEST.exists():
    raise SystemExit("ABORT: stage-02 already exists; never overwrite test artifacts: " + str(DEST))

plans = []
for game in GAMES:
    source_config = SRC / CFG_REL / (game + ".cfg")
    source_launcher = SRC / PORTS_REL / ("J2ME_" + game.replace("-", "_") + "_Profile_Test.sh")
    if not source_config.is_file() or not source_launcher.is_file():
        raise SystemExit("ABORT: missing stage-01 input for " + game)
    cfg = source_config.read_text(encoding="ascii")
    launcher = source_launcher.read_text(encoding="ascii")
    for expected in (
        'video_force_aspect = "true"',
        'video_aspect_ratio_auto = "true"',
        'config_save_on_exit = "false"',
    ):
        if cfg.count(expected) != 1:
            raise SystemExit("ABORT: baseline config does not contain expected key: " + expected)
    old_cfgpath = CARD + "/J2ME/profile-test-01/launcher-config/" + game + ".cfg"
    new_cfgpath = CARD + "/J2ME/profile-test-02/launcher-config/" + game + ".cfg"
    old_logpath = CARD + "/J2ME/logs/profile-test-" + game + ".log"
    new_logpath = CARD + "/J2ME/logs/profile-aspect-02-" + game + ".log"
    if launcher.count(old_cfgpath) != 1 or launcher.count(old_logpath) != 1:
        raise SystemExit("ABORT: baseline launcher paths changed: " + game)
    if "auto_overrides_enable =" in cfg:
        raise SystemExit("ABORT: stage-01 already has auto overrides setting: " + game)

    cfg = cfg.rstrip("\n") + (
        "\n# Stage-02 diagnostic: prevent late core/game overrides from replacing\n"
        "# the startup aspect setting applied by --appendconfig.\n"
        'auto_overrides_enable = "false"\n'
    )
    launcher = launcher.replace(old_cfgpath, new_cfgpath).replace(old_logpath, new_logpath)
    launcher = launcher.replace("J2ME PROFILE TEST", "J2ME ASPECT DIAGNOSTIC 02")
    plans.append((game, cfg, launcher))

for game, cfg, launcher in plans:
    new_config = DEST / "J2ME" / "profile-test-02" / "launcher-config" / (game + ".cfg")
    new_launcher = DEST / PORTS_REL / ("J2ME_" + game.replace("-", "_") + "_Aspect_Test.sh")
    new_config.parent.mkdir(parents=True, exist_ok=True)
    new_launcher.parent.mkdir(parents=True, exist_ok=True)
    new_config.write_text(cfg, encoding="ascii")
    new_launcher.write_text(launcher, encoding="ascii")
    new_launcher.chmod(0o755)
    print("STAGED:", game, "auto_overrides_enable=false")

print("ASPECT_02_STAGE_OK:", DEST)
print("This test reuses stage-01 core-option .opt files already copied to TF2.")
for p in sorted(DEST.rglob("*")):
    if p.is_file():
        print(" ", p.relative_to(DEST))
