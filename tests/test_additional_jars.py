#!/usr/bin/env python3
"""Offline host tests: never touch any attached TF1/TF2 card."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "scripts" / "stage-additional-jars.py"
KNOWN = ("Bounce.jar", "Diamond Rush.jar")
EXTRAS = (
    "Bounce Tales.jar",
    "Tower Bloxx.jar",
    "The Sims Bowling.jar",
    "James Camerons Avatar.jar",
)


class AdditiveJarsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="rg35xx-jars-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.roms = self.root / "roms"
        self.roms.mkdir()
        self.dest = self.root / "additive"
        for name in KNOWN + EXTRAS:
            (self.roms / name).write_bytes(b"not a game; filename scan only")

    def run_stage(self, *args):
        return subprocess.run(
            [sys.executable, str(PROGRAM), str(self.dest),
             "--rom-dir", str(self.roms), *args],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )

    def test_four_user_candidates_generate_only_additions(self):
        result = self.run_stage()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ADDITIVE_STAGE_OK", result.stdout)
        plan = json.loads((self.dest / ".host-only/install-plan.json").read_text())
        self.assertEqual(len(plan["games"]), 4)
        self.assertEqual(
            {g["rom_file"] for g in plan["games"]}, set(EXTRAS)
        )
        self.assertEqual(len(plan["files"]), 16)
        self.assertFalse((self.dest / "J2ME/universal-v1/dispatch.sh").exists())
        self.assertFalse((self.dest / "J2ME/universal-v1/options/bounce.opt").exists())
        self.assertFalse((self.dest / "Roms/PORTS/J2ME_bounce.sh").exists())
        self.assertFalse((self.dest / "Roms/PORTS/J2ME_diamond_rush.sh").exists())
        for g in plan["games"]:
            expected_resolution = "360x360" if g["rom_file"] == "The Sims Bowling.jar" else "240x320"
            self.assertEqual(g["resolution"], expected_resolution)
            self.assertEqual(g["sound"], "off")
            self.assertEqual(g["backlight"], "Disabled")
            base = self.dest / "J2ME/universal-v1"
            cfg = (base / "launcher-config" / (g["id"] + ".cfg")).read_text()
            self.assertIn('video_dingux_ipu_keep_aspect = "true"', cfg)
            self.assertNotIn("auto_overrides_enable", cfg)
            opts = (base / "options" / (g["id"] + ".opt")).read_text()
            self.assertIn('freej2me_resolution = "' + expected_resolution + '"', opts)
            launcher = self.dest / "Roms/PORTS" / (
                "J2ME_" + g["id"].replace("-", "_") + ".sh")
            self.assertEqual(subprocess.run(["sh", "-n", str(launcher)]).returncode, 0)
            self.assertIn("exec /bin/sh", launcher.read_text())
        for item in plan["files"]:
            content = (self.dest / item["path"]).read_bytes()
            self.assertEqual(item["sha256"], hashlib.sha256(content).hexdigest())
        self.assertEqual(len([p for p in self.dest.rglob("*") if p.is_file()]), 17)
        for original in KNOWN + EXTRAS:
            self.assertTrue((self.roms / original).exists())

    def test_sims_bowling_verified_resolution_preserves_auto_id(self):
        result = self.run_stage("--only", "The Sims Bowling.jar")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads((self.dest / ".host-only/install-plan.json").read_text())
        self.assertEqual(len(plan["games"]), 1)
        game = plan["games"][0]
        self.assertEqual(game["id"], "auto-the-sims-bowling-c00b0e66")
        self.assertEqual(game["resolution"], "360x360")
        self.assertIn("VERIFIED PROFILE: The Sims Bowling.jar 360x360", result.stdout)
        self.assertEqual(len(plan["files"]), 4)
        opts = (self.dest / "J2ME/universal-v1/options" /
                (game["id"] + ".opt")).read_text()
        self.assertIn('freej2me_resolution = "360x360"', opts)

    def test_second_stage_fails_without_changes(self):
        self.assertEqual(self.run_stage().returncode, 0)
        before = {p.relative_to(self.dest): p.read_bytes()
                  for p in self.dest.rglob("*") if p.is_file()}
        result = self.run_stage()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination exists", result.stderr)
        after = {p.relative_to(self.dest): p.read_bytes()
                 for p in self.dest.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_only_one_candidate_can_be_staged(self):
        result = self.run_stage("--only", "Tower Bloxx.jar")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads((self.dest / ".host-only/install-plan.json").read_text())
        self.assertEqual(len(plan["games"]), 1)
        self.assertEqual(plan["games"][0]["rom_file"], "Tower Bloxx.jar")
        self.assertEqual(len(plan["files"]), 4)

    def test_known_or_missing_jar_not_a_new_candidate(self):
        for value in ("Bounce.jar", "Does Not Exist.jar"):
            with self.subTest(value=value):
                result = self.run_stage("--only", value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("--only must name", result.stderr)
                self.assertFalse(self.dest.exists())

    def test_missing_known_jar_fails_before_staging(self):
        (self.roms / "Bounce.jar").unlink()
        result = self.run_stage()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("known JAR missing", result.stderr)
        self.assertFalse(self.dest.exists())

    def test_unsafe_name_is_not_staged(self):
        (self.roms / "Command;Injection.jar").write_bytes(b"test")
        result = self.run_stage()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SKIP UNSAFE FILENAME", result.stdout)
        plan = json.loads((self.dest / ".host-only/install-plan.json").read_text())
        self.assertEqual(len(plan["games"]), 4)

    def test_missing_extra_files_gives_no_addition(self):
        for name in EXTRAS:
            (self.roms / name).unlink()
        result = self.run_stage()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No new safe JAR", result.stderr)
        self.assertFalse(self.dest.exists())


if __name__ == "__main__":
    unittest.main()
