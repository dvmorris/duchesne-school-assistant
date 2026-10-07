# Duchesne School Assistant — Cross-Platform Packaging & Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package and distribute the Duchesne School Assistant for parents across Claude, Gemini, ChatGPT/OpenAI, and local agent environments, enabling true zero-code 1-click installation via GitHub repository URL sync (`https://github.com/dvmorris/duchesne-school-assistant`), native marketplace manifests, web chat prompts, and a parent-friendly README.

**Architecture:** Implement native Claude marketplace manifests (`.claude-plugin/marketplace.json`, `plugin.json`), canonical master knowledge base (`distribution/common/duchesne_knowledge_base.md`), 1-click calendar links (`distribution/common/calendar_links.md`), web chat universal prompts (`distribution/web/universal_parent_prompt.md`), and a comprehensive parent welcome guide in `README.md`. Verify all manifests, links, 12 social channels, and onboarding flows with an automated test suite in `tests/test_distribution.py`.

**Tech Stack:** Python 3 standard library (`json`, `re`, `unittest`, `pathlib`, `urllib`), GitHub Flavored Markdown, Claude Plugin Marketplace spec.

**Spec:** `docs/superpowers/specs/2026-10-06-duchesne-cross-platform-distribution-design.md`

## Global Constraints
- Target repository URL: `https://github.com/dvmorris/duchesne-school-assistant` (exact match).
- Zero external pip dependencies (strictly standard library).
- Zero password requirement: Assistant strictly never prompts for or stores Veracross credentials or sensitive student records.
- All 12 registered social media channels must be accurately represented across distribution assets.
- All unit and integration tests must pass cleanly.

---

### Task 1: Native Claude Plugin & Marketplace Manifests

**Files:**
- Create: `.claude-plugin/marketplace.json`
- Create: `.claude-plugin/plugin.json`
- Test: `tests/test_distribution.py`

**Interfaces:**
- Produces: Valid Claude marketplace registry and plugin metadata files discoverable via `https://github.com/dvmorris/duchesne-school-assistant`.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_distribution.py`  
Expected: FAIL with missing file or test not found.

- [ ] **Step 3: Write minimal implementation**

Create `.claude-plugin/marketplace.json`:
```json
{
  "name": "duchesne-parent-marketplace",
  "owner": {
    "name": "Duchesne Academy Parents",
    "email": "support@duchesne-assistant.local"
  },
  "plugins": [
    {
      "name": "duchesne-school-assistant",
      "description": "Duchesne Academy parent companion: schedules, uniform rules, dining, portals, and digests",
      "version": "1.0.0",
      "source": {
        "source": "url",
        "url": "https://github.com/dvmorris/duchesne-school-assistant.git"
      }
    }
  ]
}
```

Create `.claude-plugin/plugin.json`:
```json
{
  "name": "duchesne-school-assistant",
  "version": "1.0.0",
  "description": "Duchesne Academy parent companion for multi-division schedules, Veracross portals, Toddle, Nutrislice, Spirit Store, and social media digests.",
  "author": {
    "name": "Duchesne Academy Parents"
  },
  "homepage": "https://github.com/dvmorris/duchesne-school-assistant",
  "repository": "https://github.com/dvmorris/duchesne-school-assistant",
  "entrypoint": "scripts/veracross_scanner.py",
  "skills": [
    {
      "name": "duchesne-school-assistant",
      "path": "SKILL.md"
    }
  ]
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_distribution.py`  
Expected: PASS (2 tests passed).

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/marketplace.json .claude-plugin/plugin.json tests/test_distribution.py
git commit -m "feat(distribution): add native Claude plugin and marketplace manifests"
```

---

### Task 2: Canonical Master Knowledge Base & Calendar Subscriptions

**Files:**
- Create: `distribution/common/duchesne_knowledge_base.md`
- Create: `distribution/common/calendar_links.md`
- Modify: `tests/test_distribution.py`

**Interfaces:**
- Produces: Standalone markdown reference documenting campus hours, division contacts, bell schedules, uniform rules, dining, portals, all 12 registered social media accounts, and 1-click calendar links.

- [ ] **Step 1: Write the failing test**

In `tests/test_distribution.py`:
```python
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
        self.assertIn("10:55 AM", content) # PK4 lunch

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_distribution.py`  
Expected: FAIL with missing knowledge base files.

- [ ] **Step 3: Write minimal implementation**

Create `distribution/common/duchesne_knowledge_base.md` containing full school specifications, uniform rules, bell schedules, dining details, all 12 social media channel links, and the Zero-Password security policy.

Create `distribution/common/calendar_links.md` containing 1-click subscription links for Apple (`webcal://`), Google, and Outlook.

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_distribution.py`  
Expected: PASS (4 tests passed).

- [ ] **Step 5: Commit**

```bash
git add distribution/common/duchesne_knowledge_base.md distribution/common/calendar_links.md tests/test_distribution.py
git commit -m "feat(distribution): add canonical master knowledge base and 1-click calendar links"
```

---

### Task 3: Web Chat Universal Parent Prompt & Setup Guide

**Files:**
- Create: `distribution/web/universal_parent_prompt.md`
- Create: `distribution/web/setup_guide.md`
- Modify: `tests/test_distribution.py`

**Interfaces:**
- Produces: Self-contained, copy-pasteable parent prompt for web chat users (ChatGPT, Claude, Gemini) with hybrid onboarding and privacy guardrails.

- [ ] **Step 1: Write the failing test**

In `tests/test_distribution.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_distribution.py`  
Expected: FAIL with missing universal prompt.

- [ ] **Step 3: Write minimal implementation**

Create `distribution/web/universal_parent_prompt.md`:
- Includes persona, hybrid onboarding greeting, division-aware filtering, email summarization instructions, Spirit Store recommendations, and strict zero-password privacy rules.

Create `distribution/web/setup_guide.md`:
- Quick 3-step guide for pasting into `chatgpt.com`, `claude.ai`, or `gemini.google.com`.

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_distribution.py`  
Expected: PASS (5 tests passed).

- [ ] **Step 5: Commit**

```bash
git add distribution/web/universal_parent_prompt.md distribution/web/setup_guide.md tests/test_distribution.py
git commit -m "feat(distribution): add universal web chat parent prompt and setup guide"
```

---

### Task 4: Parent-Friendly Root README.md

**Files:**
- Create: `README.md`
- Modify: `tests/test_distribution.py`

**Interfaces:**
- Produces: Front-page parent welcome guide featuring direct GitHub repository sync (`https://github.com/dvmorris/duchesne-school-assistant`), step-by-step instructions for Claude, Gemini, ChatGPT, Option B ZIP upload, 1-tap mobile calendar buttons, and advanced CLI options.

- [ ] **Step 1: Write the failing test**

In `tests/test_distribution.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_distribution.py`  
Expected: FAIL (README.md does not exist yet).

- [ ] **Step 3: Write minimal implementation**

Create `README.md` in repository root with:
1. Hero header and Duchesne branding.
2. Method 1: Direct Sync via GitHub Link (Easiest — Under 1 Minute) for Claude Web/Desktop, Gemini, and ChatGPT.
3. Method 2: Drag-and-Drop / Upload ZIP (No URL Needed).
4. Method 3: 1-Tap Mobile & Laptop Calendar Subscriptions (`webcal://`, Google, Outlook).
5. Method 4: Advanced CLI / Developer Setup (`python3 scripts/veracross_scanner.py`).
6. Privacy & Security Guarantee (Zero-Password Manifesto).

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_distribution.py`  
Expected: PASS (6 tests passed).

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_distribution.py
git commit -m "docs: add parent-friendly root README with 1-click GitHub sync instructions"
```

---

### Task 5: Final Distribution Verification & Workspace Sync

**Files:**
- Modify: `SKILL.md` (add distribution reference to Quick Reference)
- Verify: Full test suite (`tests/`)
- Sync: `~/ge_spark_workspace/skills/duchesne-school-assistant/`

- [ ] **Step 1: Run full test suite**

Run: `PYTHONPATH=. python3 -m unittest discover -v -s tests`  
Expected: PASS (79+ tests passed).

- [ ] **Step 2: Update SKILL.md**

Update `SKILL.md` to reference `.claude-plugin/` and `distribution/` assets.

- [ ] **Step 3: Sync to mirror workspace**

Run: `rsync -av --exclude '.git' --exclude '__pycache__' --exclude '.superpowers' ./ /Users/davemorris/ge_spark_workspace/skills/duchesne-school-assistant/`  
Expected: Transfer clean.

- [ ] **Step 4: Commit and finalize**

```bash
git add SKILL.md
git commit -m "docs(skill): update SKILL.md with cross-platform distribution references"
```
