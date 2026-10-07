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
        self.assertIn("dvmorris/duchesne-school-assistant", plugins[0]["source"]["url"])

    def test_claude_plugin_json(self):
        plugin_path = REPO_ROOT / ".claude-plugin" / "plugin.json"
        self.assertTrue(plugin_path.exists(), "plugin.json missing")
        with open(plugin_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("name"), "duchesne-school-assistant")
        self.assertEqual(data.get("version"), "1.0.0")
        self.assertEqual(data.get("repository"), "https://github.com/dvmorris/duchesne-school-assistant")
        self.assertEqual(data.get("skills", [])[0]["name"], "duchesne-school-assistant")
