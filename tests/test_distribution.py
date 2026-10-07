import os
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

class TestDistributionManifests(unittest.TestCase):
    def test_claude_marketplace_json(self):
        marketplace_path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
        self.assertTrue(marketplace_path.exists(), "marketplace.json missing")
        with open(marketplace_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("name"), "duchesne-parent-marketplace")
        plugins = data.get("plugins", [])
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0].get("name"), "duchesne-school-assistant")
        self.assertEqual(plugins[0]["source"]["url"], "https://github.com/dvmorris/duchesne-school-assistant")

    def test_claude_plugin_json(self):
        plugin_path = REPO_ROOT / ".claude-plugin" / "plugin.json"
        self.assertTrue(plugin_path.exists(), "plugin.json missing")
        with open(plugin_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("name"), "duchesne-school-assistant")
        self.assertEqual(data.get("version"), "1.0.0")
        self.assertEqual(data.get("repository"), "https://github.com/dvmorris/duchesne-school-assistant")
        self.assertEqual(data.get("skills", [])[0]["name"], "duchesne-school-assistant")


class TestDistributionContent(unittest.TestCase):
    def test_master_knowledge_base_content(self):
        kb_path = REPO_ROOT / "distribution" / "common" / "duchesne_knowledge_base.md"
        self.assertTrue(kb_path.exists())
        with open(kb_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check campus and hours
        self.assertIn("10202 Memorial Dr, Houston, TX 77024", content)
        self.assertIn("Lower School (PK3–Grade 4)", content)
        self.assertIn("Middle School (Grades 5–8)", content)
        self.assertIn("Upper School (Grades 9–12)", content)
        self.assertIn("10:55 AM", content)  # PK4 lunch

        # Check portals
        self.assertIn("https://portals.veracross.com/duchesne/parent", content)
        self.assertIn("https://web.toddleapp.com", content)
        self.assertIn("https://duchesnespiritstore.square.site/", content)
        self.assertIn("https://duchesne.nutrislice.com/", content)

        # Check 12 social channels
        expected_channels = [
            "instagram.com/duchesnehouston",
            "instagram.com/duchesneathletics",
            "instagram.com/chargergirlsdance",
            "instagram.com/duchesne_arts",
            "instagram.com/duchesneupperschool",
            "instagram.com/duchesneadmissions",
            "instagram.com/duchesnealumnae",
            "linkedin.com/school/duchesne-academy-of-the-sacred-heart",
            "facebook.com/DuchesneAcademyHouston",
            "facebook.com/profile.php?id=100079069373448",
            "facebook.com/DuchesneHoustonAlums",
            "youtube.com/@duchesneacademyofthesacred1409"
        ]
        for ch in expected_channels:
            self.assertIn(ch, content)

        # Check zero-password rule
        self.assertIn("Zero-Password", content)

    def test_calendar_links_content(self):
        cal_path = REPO_ROOT / "distribution" / "common" / "calendar_links.md"
        self.assertTrue(cal_path.exists())
        with open(cal_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("webcal://portals.veracross.com/duchesne/subscribe/", content)
        self.assertIn("calendar.google.com/calendar/r?cid=", content)

    def test_universal_parent_prompt_content(self):
        prompt_path = REPO_ROOT / "distribution" / "web" / "universal_parent_prompt.md"
        self.assertTrue(prompt_path.exists())
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Hybrid onboarding
        self.assertIn("Welcome to the Duchesne School Assistant", content)
        self.assertIn("division", content.lower())
        self.assertIn("grade", content.lower())

        # Zero password privacy
        self.assertIn("NEVER ask for or accept Veracross passwords", content)

        # Core capabilities
        self.assertIn("Spirit Store", content)
        self.assertIn("Social Media", content)
        self.assertIn("Veracross", content)

        # Web setup guide
        guide_path = REPO_ROOT / "distribution" / "web" / "setup_guide.md"
        self.assertTrue(guide_path.exists())
        with open(guide_path, "r", encoding="utf-8") as f:
            guide_content = f.read()
        self.assertIn("chatgpt.com", guide_content.lower())
        self.assertIn("claude.ai", guide_content.lower())
        self.assertIn("gemini.google.com", guide_content.lower())

    def test_root_readme_parent_guide(self):
        readme_path = REPO_ROOT / "README.md"
        self.assertTrue(readme_path.exists())
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Target repo URL
        self.assertIn("https://github.com/dvmorris/duchesne-school-assistant", content)

        # Platform sync instructions
        self.assertIn("Claude", content)
        self.assertIn("Add marketplace", content)
        self.assertIn("Sync", content)
        self.assertIn("Gemini", content)
        self.assertIn("ChatGPT", content)

        # Option B
        self.assertIn("Download ZIP", content)

        # Privacy
        self.assertIn("Zero-Password", content)



