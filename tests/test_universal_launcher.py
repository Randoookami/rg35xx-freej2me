#!/usr/bin/env python3
"""Host-side tests for the RG35XX universal launcher generator.

No microSD card or RG35XX hardware is accessed.
Run: python3 -m unittest discover -s tests -p 'test_universal_launcher.py' -v
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "stage-universal-launcher.py"


def run_generator(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(a) for a in args)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )


class UniversalLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="j2me-launcher-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.stage = self.path / "stage"

    def test_known_profiles_share_one_dispatcher(self):
        result = run_generator(self.stage)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("UNIVERSAL_STAGE_OK", result.stdout)
        dispatcher = self.stage / "J2ME/universal-v1/dispatch.sh"
        self.assertTrue(dispatcher.exists())
        for game_id, resolution in (("bounce", "128x128"),
                                    ("diamond-rush", "176x208")):
            base = self.stage / "J2ME/universal-v1"
            cfg = (base / "launcher-config" / (game_id + ".cfg")).read_text()
            opt = (base / "options" / (game_id + ".opt")).read_text()
            launcher = self.stage / "Roms/PORTS" / (
                "J2ME_" + game_id.replace("-", "_") + ".sh")
            launcher_text = launcher.read_text()
            self.assertIn('video_dingux_ipu_keep_aspect = "true"', cfg)
            self.assertIn('load_dummy_on_core_shutdown = "false"', cfg)
            self.assertIn('config_save_on_exit = "false"', cfg)
            self.assertNotIn("auto_overrides_enable", cfg)
            self.assertIn('freej2me_resolution = "' + resolution + '"', opt)
            self.assertIn('freej2me_sound = "off"', opt)
            self.assertIn("/mnt/SDCARD/J2ME/universal-v1/dispatch.sh", launcher_text)
            self.assertNotIn("retroarch", launcher_text)
            self.assertIn("exec /bin/sh", launcher_text)
            self.assertEqual(subprocess.run(["sh", "-n", str(launcher)]).returncode, 0)
        self.assertEqual(subprocess.run(["sh", "-n", str(dispatcher)]).returncode, 0)
        files = [p for p in self.stage.rglob("*") if p.is_file()]
        self.assertEqual(len(files), 10)  # shared + manifest + four per known game

    def test_fails_closed_when_stage_exists(self):
        self.assertEqual(run_generator(self.stage).returncode, 0)
        before = {p.relative_to(self.stage): p.read_bytes()
                  for p in self.stage.rglob("*") if p.is_file()}
        result = run_generator(self.stage)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination exists", result.stderr)
        after = {p.relative_to(self.stage): p.read_bytes()
                 for p in self.stage.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_scan_unknown_jar_assigns_safe_defaults(self):
        roms = self.path / "read-only-roms"
        roms.mkdir()
        for name in ("Bounce.jar", "Diamond Rush.jar", "Other Game.jar"):
            (roms / name).write_bytes(b"dummy - only filename is inspected")
        result = run_generator(self.stage, "--rom-dir", roms)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((self.stage / "J2ME/universal-v1/staged-profiles.json").read_text())
        self.assertEqual(len(manifest["games"]), 3)
        unknown = [g for g in manifest["games"] if g["rom_file"] == "Other Game.jar"]
        self.assertEqual(len(unknown), 1)
        game = unknown[0]
        self.assertEqual(game["resolution"], "240x320")
        self.assertEqual(game["sound"], "off")
        self.assertEqual(game["backlight"], "Disabled")
        self.assertTrue((self.stage / "J2ME/universal-v1/options" /
                         (game["id"] + ".opt")).exists())
        self.assertTrue((roms / "Other Game.jar").exists())

    def test_missing_known_rom_is_error_before_any_output(self):
        roms = self.path / "read-only-roms"
        roms.mkdir()
        (roms / "Bounce.jar").write_bytes(b"test")
        result = run_generator(self.stage, "--rom-dir", roms)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("known JAR missing", result.stderr)
        self.assertFalse(self.stage.exists())

    def test_unsafe_unknown_filename_is_skipped(self):
        roms = self.path / "read-only-roms"
        roms.mkdir()
        for name in ("Bounce.jar", "Diamond Rush.jar", "Weird;Name.jar"):
            (roms / name).write_bytes(b"dummy")
        result = run_generator(self.stage, "--rom-dir", roms)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SKIP UNSAFE FILENAME", result.stdout)
        data = json.loads((self.stage / "J2ME/universal-v1/staged-profiles.json").read_text())
        self.assertEqual(len(data["games"]), 2)


if __name__ == "__main__":
    unittest.main()
