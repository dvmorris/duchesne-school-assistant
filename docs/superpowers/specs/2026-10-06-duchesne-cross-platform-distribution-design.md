# Duchesne School Assistant — Cross-Platform Packaging & Distribution Design Spec

**Date:** 2026-10-06  
**Status:** Approved  
**Repository:** `https://github.com/dvmorris/duchesne-school-assistant`  
**Sub-Project:** 3 of 3 (Cross-Platform Packaging & Distribution)  

---

## 1. Executive Summary & Purpose

The **Duchesne School Assistant** has established a multi-division Veracross core (Sub-Project 1) and extended feature crawlers for the Duchesne Spirit Store, parent contact directories, and a 12-channel social media aggregator (Sub-Project 2).

Sub-Project 3 packages the assistant for widespread distribution among parents of Duchesne Academy of the Sacred Heart across all major modern AI platforms (**Claude**, **Gemini**, **ChatGPT / OpenAI**, and local agent environments). 

Crucially, **school parents must not be expected to use terminal commands, git, or code.** The distribution model relies on:
1. **Direct GitHub Sync (Easiest / 1-Click):** Parents simply copy `https://github.com/dvmorris/duchesne-school-assistant` and paste it into their AI app's "Add from repository / Marketplace" settings.
2. **Native Skill Manifests:** Claude Code / Claude Desktop plugins (`.claude-plugin/marketplace.json` and `plugin.json`), Gemini Skills, and universal agent standards.
3. **Web Chat Drag-and-Drop / Copy-Paste:** For parents using web browser chat windows (`chatgpt.com`, `claude.ai`, `gemini.google.com`), a self-contained parent prompt and pre-packaged knowledge guide.
4. **1-Tap Mobile Calendar Links:** Native `webcal://` and Google/Outlook calendar subscription buttons.
5. **Strict Zero-Password Privacy Architecture:** Explicit policies guaranteeing no Veracross credentials or sensitive student records are ever requested or stored.

---

## 2. Distribution Architecture & File Layout

```
duchesne-school-assistant/
├── .claude-plugin/
│   ├── marketplace.json                # Claude Plugin Marketplace registry manifest
│   └── plugin.json                     # Claude Plugin specification manifest
├── README.md                           # Parent Welcome & 1-Minute Setup Guide
├── SKILL.md                            # Universal Agent Skill definition (Gemini / Claude / OpenAI)
├── distribution/
│   ├── common/
│   │   ├── duchesne_knowledge_base.md  # Master reference: schedules, divisions, links, 12 social channels
│   │   └── calendar_links.md           # 1-click subscription links (Apple webcal://, Google, Outlook)
│   └── web/
│       ├── universal_parent_prompt.md  # Single copy-paste prompt for web ChatGPT, Claude, or Gemini
│       └── setup_guide.md              # 2-minute instructions for web chat parents
└── tests/
    └── test_distribution.py            # Automated integrity tests for manifests, URLs, channels, and README
```

---

## 3. Native Platform Discovery Manifests

### 3.1 Claude Marketplace & Plugin Manifests (`.claude-plugin/`)

Claude supports adding plugins directly from GitHub repositories via **Settings > Customize > Plugins > Add Marketplace / Add from repository**.

#### `.claude-plugin/marketplace.json`
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

#### `.claude-plugin/plugin.json`
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

---

## 4. Master Knowledge Base (`duchesne_knowledge_base.md`)

The canonical source of truth for general Duchesne Academy information:

### 4.1 Campus & Division Essentials
- **School Address:** Duchesne Academy of the Sacred Heart, 10202 Memorial Dr, Houston, TX 77024.
- **Main Phone:** (713) 468-8211.
- **Divisions & Hours:**
  - **Lower School (PK3–Grade 4):** 7:55 AM – 3:15 PM (PK3/PK4 dismissal options; PK4 lunch at 10:55 AM).
  - **Middle School (Grades 5–8):** 7:55 AM – 3:30 PM.
  - **Upper School (Grades 9–12):** 8:00 AM – 3:30 PM.
- **Uniforms:** Mills Uniform Company; Formal dress days vs. Friday Spirit wear rules.
- **Dining:** Sage Dining Services menus via Nutrislice (`https://duchesne.nutrislice.com/`).

### 4.2 Digital Portals & Shortcuts
- **Veracross Parent Portal:** `https://portals.veracross.com/duchesne/parent`
- **Veracross Communication Settings:** Top-right profile icon > *Manage School Communication*
- **Toddle LMS (Lower School):** `https://web.toddleapp.com`
- **Duchesne Spirit Store:** `https://duchesnespiritstore.square.site/`
- **Nutrislice Lunch Menus:** `https://duchesne.nutrislice.com/`
- **Magnus Health Portal:** Accessed via Veracross single sign-on

### 4.3 All 12 Official Social Media Accounts
1. **Instagram (Main):** `https://www.instagram.com/duchesnehouston`
2. **Instagram (Athletics):** `https://www.instagram.com/duchesneathletics`
3. **Instagram (Charger Girls Dance):** `https://www.instagram.com/chargergirlsdance/`
4. **Instagram (Fine Arts):** `https://www.instagram.com/duchesne_arts/`
5. **Instagram (Upper School):** `https://www.instagram.com/duchesneupperschool`
6. **Instagram (Admissions):** `https://www.instagram.com/duchesneadmissions/`
7. **Instagram (Alumnae):** `https://www.instagram.com/duchesnealumnae`
8. **LinkedIn:** `https://www.linkedin.com/school/duchesne-academy-of-the-sacred-heart/`
9. **Facebook (Main):** `https://www.facebook.com/DuchesneAcademyHouston`
10. **Facebook (Athletics & Campus Life):** `https://www.facebook.com/profile.php?id=100079069373448`
11. **Facebook (Alumnae):** `https://www.facebook.com/DuchesneHoustonAlums`
12. **YouTube:** `https://www.youtube.com/@duchesneacademyofthesacred1409`

### 4.4 1-Click Calendar Subscriptions
- **Apple Calendar / iOS:** `webcal://portals.veracross.com/duchesne/subscribe/all_school.ics`
- **Google Calendar:** `https://calendar.google.com/calendar/r?cid=webcal://portals.veracross.com/duchesne/subscribe/all_school.ics`
- **Outlook:** Direct `.ics` import instructions.

---

## 5. User Experience & Hybrid Onboarding Flow

### 5.1 Zero-Password Privacy Architecture
- The assistant operates under a strict **Zero-Credential Policy**:
  - It NEVER prompts the parent for their Veracross username or password.
  - It NEVER attempts to scrape behind private authentication or store login cookies.
- For private updates:
  - **Web Chat:** Parents paste specific email text or portal announcement snippets ("Can you summarize this teacher note?").
  - **Local Agent / CLI:** Power-user parents run local offline scripts where data remains strictly on their machine.

### 5.2 Hybrid Onboarding Logic
Upon first activation in any AI environment:
1. **Interactive Prompt:**
   > *"Welcome to the Duchesne School Assistant! ❤️ Charger Pride! To personalize announcements, events, and schedules for your family, which division(s) and grade(s) are your daughter(s) in? (e.g., Lower School PK4, 7th Grade, or Upper School 10th)"*
2. **Profile Acceptance:**
   - Accepts plain text response: *"My daughter is in PK4."*
   - Accepts structured snippet or `duchesne_profile.json` upload.
3. **Session Filtering:**
   - Filters all subsequent answers and digest sections to match the family's registered divisions.

---

## 6. Parent-Friendly README.md Design

The root `README.md` is structured specifically for non-technical parents:
1. **Hero Header:** Duchesne Academy branding and clear mission statement.
2. **Method 1: Direct Sync via GitHub Link (Easiest — Under 1 Minute):**
   - Step-by-step instructions with highlighted UI terms for **Claude (Web or Desktop)**.
   - Step-by-step instructions for **Gemini**.
   - Step-by-step instructions for **ChatGPT**.
3. **Method 2: Drag-and-Drop / Upload ZIP (No URL Needed):**
   - Click "Download ZIP" on GitHub and drag into chat.
4. **Method 3: 1-Tap Phone Calendar Sync:**
   - Direct clickable badges for Apple Calendar (`webcal://`), Google Calendar, and Outlook.
5. **Advanced / Power Users:**
   - Python CLI execution (`veracross_scanner.py`, `duchesne_check.py`).
6. **Privacy & Security Guarantee:**
   - Zero-password manifesto.

---

## 7. Automated Testing Plan (`tests/test_distribution.py`)

A comprehensive test suite will verify:
1. **Manifest Validity:** `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json` are valid JSON, contain required fields, and link to `https://github.com/dvmorris/duchesne-school-assistant`.
2. **Social Channels Check:** All 12 social channel URLs are present and verified in `duchesne_knowledge_base.md` and `scripts/social_aggregator.py`.
3. **Link Integrity:** Portal links, calendar links, and Spirit Store URLs are valid and well-formed.
4. **README Guidance:** Root `README.md` includes Claude sync steps, Gemini sync steps, ChatGPT import steps, ZIP download instructions, and the zero-password privacy statement.
5. **No Broken Placeholders:** Distribution files contain zero `TODO`, `TBD`, or temporary placeholders.

---

## 8. Verification & Acceptance Criteria
- All 5 test classes pass in `tests/test_distribution.py`.
- Full project test suite passes (`unittest discover tests`).
- Codebase synced to mirror workspace (`~/ge_spark_workspace/skills/duchesne-school-assistant/`).
