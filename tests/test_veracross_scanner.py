import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCANNER_SCRIPT = str(REPO_ROOT / "scripts" / "veracross_scanner.py")
CHECK_SCRIPT = str(REPO_ROOT / "scripts" / "duchesne_check.py")

from scripts.veracross_scanner import run_scanner

class TestVeracrossScannerCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.profile_path = os.path.join(self.temp_dir.name, "test_profile.json")
        self.state_path = os.path.join(self.temp_dir.name, "test_state.json")
        self.output_path = os.path.join(self.temp_dir.name, "test_output.md")

        # Create a test profile with 2 children
        profile_data = {
            "family_id": "test_fam_123",
            "children": [
                {
                    "first_name": "Clara",
                    "last_name": "Davis",
                    "division": "lower_school",
                    "grade": "PK4",
                    "homeroom_advisor": "Faculty, Sample"
                },
                {
                    "first_name": "Maya",
                    "last_name": "Davis",
                    "division": "middle_school",
                    "grade": "7",
                    "homeroom_advisor": "Advisor, Sample"
                }
            ],
            "active_dashboards": ["lower_school", "middle_school"]
        }
        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_help(self):
        res = subprocess.run(
            [sys.executable, SCANNER_SCRIPT, "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("--action", res.stdout)
        self.assertIn("--profile", res.stdout)

    def test_cli_audit_comm(self):
        res = subprocess.run(
            [sys.executable, SCANNER_SCRIPT, "--action", "audit-comm"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Healthy", res.stdout)

    def test_cli_calendars(self):
        res = subprocess.run(
            [sys.executable, SCANNER_SCRIPT, "--action", "calendars"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Subscribe to Duchesne Calendars", res.stdout)
        self.assertIn("Apple Calendar", res.stdout)
        self.assertIn("Google Calendar", res.stdout)

    def test_cli_messages(self):
        res = subprocess.run(
            [sys.executable, SCANNER_SCRIPT, "--action", "messages"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Recent Veracross Messages", res.stdout)

    def test_cli_full_scan_stdout(self):
        res = subprocess.run(
            [
                sys.executable, SCANNER_SCRIPT,
                "--profile", self.profile_path,
                "--state", self.state_path,
                "--action", "full-scan"
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Duchesne Academy Updates", res.stdout)
        self.assertIn("Lower School (Clara — PK4)", res.stdout)
        self.assertIn("Middle School (Maya — 7th)", res.stdout)

    def test_cli_digest_action(self):
        res = subprocess.run(
            [
                sys.executable, SCANNER_SCRIPT,
                "--profile", self.profile_path,
                "--state", self.state_path,
                "--action", "digest"
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Duchesne Academy Updates", res.stdout)
        self.assertIn("Lower School (Clara — PK4)", res.stdout)

    def test_cli_output_file(self):
        res = subprocess.run(
            [
                sys.executable, SCANNER_SCRIPT,
                "--profile", self.profile_path,
                "--state", self.state_path,
                "--output", self.output_path
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn(f"Digest written to {self.output_path}", res.stdout)
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Duchesne Academy Updates", content)
        self.assertIn("Lower School (Clara — PK4)", content)

    def test_cli_fallback_profile_creation(self):
        fallback_path = os.path.join(self.temp_dir.name, "nonexistent_profile.json")
        res = subprocess.run(
            [
                sys.executable, SCANNER_SCRIPT,
                "--profile", fallback_path,
                "--state", self.state_path,
                "--action", "full-scan"
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(fallback_path))
        self.assertIn("Clara", res.stdout)
        self.assertIn("PK4", res.stdout)

    def test_run_scanner_direct(self):
        digest = run_scanner(profile_path=self.profile_path, action="full-scan", print_output=False)
        self.assertIn("Duchesne Academy Updates", digest)
        self.assertIn("Lower School (Clara — PK4)", digest)
        self.assertIn("Middle School (Maya — 7th)", digest)

    def test_duchesne_check_routing_scan(self):
        res = subprocess.run(
            [
                sys.executable, CHECK_SCRIPT,
                "--scan",
                "--profile", self.profile_path,
                "--action", "audit-comm"
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Healthy", res.stdout)

    def test_duchesne_check_routing_full_scan(self):
        res = subprocess.run(
            [
                sys.executable, CHECK_SCRIPT,
                "--scan",
                "--profile", self.profile_path
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Duchesne Academy Updates", res.stdout)
        self.assertIn("Lower School (Clara — PK4)", res.stdout)

    def test_duchesne_check_status_command(self):
        res = subprocess.run(
            [
                sys.executable, CHECK_SCRIPT,
                "--status"
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Duchesne Assistant State", res.stdout)

    def test_cli_store_and_social_actions(self):
        # Test store action
        res_store = subprocess.run(
            [sys.executable, SCANNER_SCRIPT, "--action", "store"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res_store.returncode, 0)
        self.assertIn("Spirit Store", res_store.stdout)

        # Test social action
        res_social = subprocess.run(
            [sys.executable, SCANNER_SCRIPT, "--action", "social"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res_social.returncode, 0)
        self.assertIn("Social Media Highlights", res_social.stdout)

    def test_cli_contacts_action(self):
        res = subprocess.run(
            [sys.executable, SCANNER_SCRIPT, "--action", "contacts"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Parent Directory", res.stdout)
        self.assertIn("Jane Doe", res.stdout)

    def test_cli_contacts_action_with_grade_filter(self):
        res = subprocess.run(
            [sys.executable, SCANNER_SCRIPT, "--action", "contacts", "--grade", "PK4"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("PK4", res.stdout)
        self.assertIn("Jane Doe", res.stdout)
        self.assertNotIn("Sophia Johnson", res.stdout)

    def test_cli_full_scan_includes_store_and_social(self):
        res = subprocess.run(
            [
                sys.executable, SCANNER_SCRIPT,
                "--profile", self.profile_path,
                "--state", self.state_path,
                "--action", "full-scan"
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Spirit Store", res.stdout)
        self.assertIn("Social Media Highlights", res.stdout)

    def test_get_current_season(self):
        from datetime import datetime
        from scripts.veracross_scanner import get_current_season

        # Fall/Winter months
        self.assertEqual(get_current_season(datetime(2026, 10, 15)), "fall")
        self.assertEqual(get_current_season(datetime(2026, 12, 25)), "fall")
        self.assertEqual(get_current_season(datetime(2026, 1, 10)), "fall")

        # Spring months
        self.assertEqual(get_current_season(datetime(2026, 3, 1)), "spring")
        self.assertEqual(get_current_season(datetime(2026, 4, 15)), "spring")
        self.assertEqual(get_current_season(datetime(2026, 5, 30)), "spring")

        # Summer / back-to-school
        self.assertEqual(get_current_season(datetime(2026, 8, 20)), "fall")

if __name__ == "__main__":
    unittest.main()
