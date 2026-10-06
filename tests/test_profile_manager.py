import unittest
import os
import json
import tempfile
from scripts.profile_manager import (
    ChildProfile,
    FamilyProfile,
    save_profile,
    load_profile,
    infer_dashboards_for_divisions,
    normalize_division
)

class TestProfileManager(unittest.TestCase):
    def test_normalize_division(self):
        self.assertEqual(normalize_division("pk3"), "lower_school")
        self.assertEqual(normalize_division("PK4"), "lower_school")
        self.assertEqual(normalize_division("K"), "lower_school")
        self.assertEqual(normalize_division("4"), "lower_school")
        self.assertEqual(normalize_division("lower_school"), "lower_school")
        self.assertEqual(normalize_division("5"), "middle_school")
        self.assertEqual(normalize_division("8"), "middle_school")
        self.assertEqual(normalize_division("MS"), "middle_school")
        self.assertEqual(normalize_division("9"), "upper_school")
        self.assertEqual(normalize_division("12"), "upper_school")
        self.assertEqual(normalize_division("us"), "upper_school")
        # Default fallback
        self.assertEqual(normalize_division("unknown_grade"), "lower_school")

    def test_infer_dashboards_for_divisions(self):
        # LS only
        dashboards_ls = infer_dashboards_for_divisions(["lower_school"], {"include_athletics": False, "include_fine_arts": True})
        self.assertIn("all_school", dashboards_ls)
        self.assertIn("lower_school", dashboards_ls)
        self.assertIn("fine_arts", dashboards_ls)
        self.assertNotIn("middle_school", dashboards_ls)
        self.assertNotIn("athletics", dashboards_ls)

        # Multi-division (LS + MS)
        dashboards_multi = infer_dashboards_for_divisions(["lower_school", "middle_school"], {"include_athletics": True, "include_fine_arts": True})
        self.assertIn("lower_school", dashboards_multi)
        self.assertIn("middle_school", dashboards_multi)
        self.assertIn("athletics", dashboards_multi)

        # Extended programs preference
        dashboards_ext = infer_dashboards_for_divisions(["upper_school"], {"include_extended_programs": True})
        self.assertIn("extended_programs", dashboards_ext)

    def test_save_and_load_profile(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name
        try:
            child1 = ChildProfile(
                first_name="Clara",
                last_name="Davis",
                division="lower_school",
                grade="PK4",
                homeroom_advisor="Faculty, Sample",
                student_id="101",
                lms="toddle",
                toddle_class_id="116643011487614044"
            )
            child2 = ChildProfile(
                first_name="Jane",
                last_name="Davis",
                division="middle_school",
                grade="7",
                homeroom_advisor="Smith, Sarah",
                student_id="102"
            )
            profile = FamilyProfile(
                family_id="household_123",
                children=[child1, child2],
                active_dashboards=["all_school", "lower_school", "middle_school"],
                preferences={"include_lunch_menus": True}
            )
            save_profile(profile, temp_path)
            loaded = load_profile(temp_path)
            self.assertEqual(loaded.family_id, "household_123")
            self.assertEqual(len(loaded.children), 2)
            self.assertEqual(loaded.children[0].first_name, "Clara")
            self.assertEqual(loaded.children[0].toddle_class_id, "116643011487614044")
            self.assertEqual(loaded.children[1].grade, "7")
            self.assertEqual(loaded.children[1].division, "middle_school")
            self.assertEqual(loaded.preferences.get("include_lunch_menus"), True)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_load_nonexistent_profile(self):
        profile = load_profile("/nonexistent/path/profile.json")
        self.assertIsInstance(profile, FamilyProfile)
        self.assertEqual(len(profile.children), 0)
        self.assertEqual(profile.family_id, "")

if __name__ == "__main__":
    unittest.main()
