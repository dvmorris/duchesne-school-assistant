---
name: duchesne-school-assistant
description: Use when monitoring, retrieving, or organizing updates from Duchesne Academy of the Sacred Heart portals (Veracross, Toddle LMS, Nutrislice lunch menus), extracting weekly PK4 homeroom newsletters, or syncing school events to Google Drive, Calendar, and Tasks.
---

# Duchesne School Assistant

Automate monitoring, authentication, extraction, deduplication, and organization of updates across Duchesne Academy of the Sacred Heart portals, parent communication channels, and Google Workspace tools.

## Quick Reference: Portals & Sources

| Portal | URL | Auth Required | Key Content |
|---|---|---|---|
| **Parent Dashboard** | `https://portals.veracross.com/duchesne/parent` | Yes (Veracross login / Google SSO) | Friday Morning Letter (~9 AM), All-School Announcements, All-School calendar |
| **Lower School Dashboard** | `https://portals.veracross.com/duchesne/parent/pages/ls-page` | Yes (Veracross session) | Head of Lower School Letter, LS rolling calendar, uniform/grade reminders |
| **Toddle LMS** | `https://web.toddleapp.com/platform/116643011487614044/courses` | Yes (Toddle login / Google SSO) | `PK4 Homeroom (PK4HR-01)` > **Home** tab: weekly newsletter graphic/doc, announcements, portfolio |
| **Lunch Menu** | `https://duchesne.nutrislice.com/menu/lower-school/lunch` | No (Public) | Daily & weekly Lower School lunch menu, allergens |
| **Fine Arts Dashboard** | `https://portals.veracross.com/duchesne/parent/pages/fa-page` | Yes (Veracross session) | Performances, ticket releases, rehearsals |
| **Extended Programs** | `https://portals.veracross.com/duchesne/parent/pages/ep-page` | Yes (Veracross session) | After-school care, enrichment programs |
| **Instagram** | `https://www.instagram.com/duchesnehouston` | No (Public) | Photos, highlights, campus event recaps |

---

## Authentication & Browser Strategy

School portals (Veracross, Toddle) require parent credentials or Google SSO. **Never ask the user for raw passwords in chat.** Instead, use persistent browser sessions or interactive browser tools:

### Method 1: Persistent Chrome Profile (Recommended for Automated Checks)
Use a dedicated Chrome profile directory (`~/.gemini/antigravity/browser_profiles/duchesne`) with Chrome DevTools or Playwright/Puppeteer:
1. Launch the browser instance using the persistent profile:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --user-data-dir="$HOME/.gemini/antigravity/browser_profiles/duchesne" \
     --remote-debugging-port=9222 \
     "https://portals.veracross.com/duchesne/parent"
   ```
2. **First Run / Expired Session:** The user completes the login once (via Google SSO or password manager).
3. **Subsequent Runs:** Session cookies, storage, and tokens persist. The agent can inspect pages in headless or minimized mode without re-authenticating.

### Method 2: Antigravity Interactive Browser (`/browser`)
When performing an interactive run or if 2FA/SSO needs manual intervention:
1. Advise the user: *"Please use the `/browser` command or complete the SSO prompt in the browser window."*
2. Navigate to the target portal (`portals.veracross.com` or `web.toddleapp.com`).
3. Once logged in, extract the DOM content, text, or snapshots.

### Method 3: Public Direct Fetch (No Login)
For Nutrislice and public announcements, fetch directly using `read_url_content` or `curl`:
```bash
# Fetch Nutrislice Lower School lunch menu page
curl -s -L "https://duchesne.nutrislice.com/menu/lower-school/lunch"
```

---

## Core Workflows

### Workflow 1: Extracting Toddle Homeroom Newsletters & Updates
1. Navigate to student's course: `https://web.toddleapp.com/platform/116643011487614044/courses`.
2. Locate homeroom: **PK4 Homeroom (PK4HR-01)**.
3. Switch to the **Home** tab to find the weekly newsletter graphic or PDF.
4. Extract the 3 core structured sections:
   - **Sophie's Space:** Prayers, Sacred Heart Goals (Goals I–V), monthly feelings, classroom duties.
   - **Learning Focus:** Number concepts, literacy (letters, sight words, phonics), science & social studies themes.
   - **Important Reminders:** Required items (e.g., 4x6 family photos), weekly library day, dress up/spirit days.
5. Check adjacent tabs:
   - **Class Announcements:** Teacher-posted updates or schedule adjustments.
   - **Portfolio:** Student work and photos uploaded by teachers.

### Workflow 2: Google Drive Archival & Upload
To ensure files are actually stored in your remote Google Drive:
1. **Locate or Create the `Duchesne` Folder:**
   - In Gemini Spark (MCP environment):
     ```python
     # Find or create Duchesne folder
     res = call_mcp_tool("gdrive", "search", {"name_exact": "Duchesne", "type": "folder"})
     if res and res.get("files"):
         folder_id = res["files"][0]["id"]
     else:
         folder = call_mcp_tool("gdrive", "mkdir", {"name": "Duchesne"})
         folder_id = folder["id"]
     ```
   - In Antigravity / Standalone script:
     Use `scripts/upload_to_gdrive.py --folder "Duchesne" --file <path>` or upload via the authenticated browser session directly to `drive.google.com`.
2. **File Naming Standard:**
   - Standard format: `Duchesne_Newsletter_YYYY-MM-DD_PK4.pdf` (or markdown summary `Duchesne_Newsletter_YYYY-MM-DD_PK4.md`).
3. **Execute Upload:**
   - In Gemini Spark:
     ```python
     call_mcp_tool("gdrive", "upload", {
         "filepath": local_path,
         "parent": folder_id
     })
     ```
   - In Antigravity:
     Run `~/.gemini/config/skills/duchesne-school-assistant/scripts/upload_to_gdrive.py --file "<local_path>" --folder "Duchesne"`
4. **Record in State:**
   - Save the uploaded file ID/URL into `~/.gemini/antigravity/duchesne_state.json` under `uploaded_files`.

### Workflow 3: Google Calendar & Google Tasks Sync
Parse extracted dates, action items, and lunch menus into structured entries:
- **PK4 Lunch Menu Events:**
  - Synchronizes the weekly Nutrislice menu to the user's Google Calendar at the exact PK4 lunch period (**10:55 AM – 11:25 AM Central**).
  - Run `node ~/.gemini/config/skills/duchesne-school-assistant/scripts/sync_lunch_to_calendar.js`.
  - Automatically generates `Duchesne_Lunch_Menu_YYYY-MM-DD.ics` and imports via Chrome CDP directly into Google Calendar (`dvmorris@gmail.com`).
  - Includes daily entrees, vegetarian alternate, sides, soups, and allergy notes.
- **Calendar Events:**
  - Weekly recurring: Library Days, PE days, Chapel/Mass uniform days.
  - One-off events: Parent conferences, division performances, school holidays.
- **Tasks (Actionable parent items):**
  - Extract supplies, photo submissions, permission slips, or book return deadlines.
  - Format title clearly: `[Duchesne PK4] Return library books` or `[Duchesne PK4] Send 4x6 family photo`.
  - Assign explicit due dates parsed from the reminder text.

### Workflow 4: Portal Announcements & Deduplication
To prevent notification fatigue, filter against previously processed updates:
1. Maintain state in `~/.gemini/antigravity/duchesne_state.json`:
   ```json
   {
     "last_check": "2026-09-04T11:00:00Z",
     "processed_ids": ["ls_letter_20260901", "head_letter_20260829"],
     "last_newsletter_date": "2026-08-31"
   }
   ```
2. On every check, calculate a hash or extract the portal ID for each announcement.
### Workflow 5: Toddle Photo Extraction & Google Photos Sync with Metadata
Automatically download class photos posted in the Toddle Portfolio tab, attach rich metadata, and upload to Google Photos:
1. **Locate Portfolio Media:**
   - In Toddle (`web.toddleapp.com`), switch to the **Portfolio** tab for the homeroom class.
   - Extract post cards containing tagged student updates (e.g. `SubjectJournalCard` elements).
2. **Extract Rich Metadata:**
   - **Post Caption / Comments:** Teacher's note (e.g., *"B is for Banana Bread 🍌"*, *"Morning work stations 😊"*).
   - **Teacher Name:** e.g., `Faculty, Lower School`, `Faculty, Lower School`, `Faculty, Sample`.
   - **Student Tagged:** `Davis, Clara`.
   - **Date / Timestamp:** e.g., `2026-09-04`, `31 Aug 2026`.
3. **Download & Stamp EXIF Metadata:**
   - Run `node ~/.gemini/config/skills/duchesne-school-assistant/scripts/sync_toddle_photos.js` to download full-resolution images and extract precise post dates.
   - Run `python3 ~/.gemini/config/skills/duchesne-school-assistant/scripts/tag_and_upload_photos.py` to embed:
     - **Image Description (EXIF 270):** Comments, teacher attribution, student name:
       ```text
       [Duchesne Academy - PK4] Pete the Cat with a special guest in guitar- Mr. Gallaher from upper school! | Teacher: Faculty, Sample | Student: Davis, Clara | Toddle: 2026:08:27 10:27:00
       ```
     - **Capture Timestamps (EXIF 36867 `DateTimeOriginal`, 36868 `DateTimeDigitized`, 306 `DateTime`):** Exact Toddle post time (e.g., `2026:08:27 10:27:00`).
     - **Filesystem mtime:** Matched to the original post timestamp.
     - This ensures Google Photos automatically indexes and places photos under their actual capture dates (e.g. August 27, 2026, August 31, 2026) rather than today's upload date.
4. **Google Photos & Drive Storage:**
   - **Google Photos (Browser-Driven, Zero-Config):** Run `node ~/.gemini/config/skills/duchesne-school-assistant/scripts/upload_photos_browser.js` to upload all photos directly through the authenticated browser window using Chrome DevTools Protocol (CDP) file chooser interception (`DOM.setFileInputFiles`). No Google Cloud API keys or OAuth credentials required.
   - **Google Photos (OAuth API fallback):** Can alternatively upload via `photoslibrary.googleapis.com/v1/mediaItems:batchCreate` if OAuth tokens are configured via `scripts/setup_oauth.py`.
   - **Local & Drive Mirror:** Files are preserved in `~/Pictures/Duchesne PK4/` and mirrored in `~/Google Drive/Duchesne/Photos/`.
5. **Deduplication:**
   - Records processed image IDs in `~/.gemini/antigravity/duchesne_state.json` under `processed_photos` so duplicate images are never re-downloaded or re-uploaded.


---

## Output Format

Always format the synthesized report using clear, citable headings:

```markdown
# Duchesne Academy Updates — [Date]

### 📌 Urgent & Actionable Items
- [ ] **Action Item 1** (Due: YYYY-MM-DD) — Source: [Veracross/Toddle]
- [ ] **Action Item 2** (Due: YYYY-MM-DD)

### 📬 Letters & Announcements
- **Head of School Friday Letter:** [Key takeaways & links]
- **Lower School Head Letter:** [Grade-level updates]

### 🎒 PK4 Homeroom Newsletter (Lower School)
- **Sophie's Space:** [Sacred Heart Goal, class focus]
- **Learning Focus:** [Math, Literacy, Science highlights]
- **Reminders:** [Library day, photos, upcoming events]

### 🥗 Lower School Lunch Menu (Upcoming Days)
- **Monday:** [Menu items]
- **Tuesday:** [Menu items]

### 🗄️ Archival & Sync Status
- Google Drive: Saved `Duchesne_Newsletter_YYYY-MM-DD_PK4.pdf`
- Google Calendar: Added [N] events
- Google Tasks: Added [N] tasks
```

---

## Common Mistakes & Edge Cases

| Issue | Cause | Fix |
|---|---|---|
| **Auth redirect loop** | Stale cookies in persistent browser profile | Delete cookies or prompt user to re-authenticate via Google SSO in the browser window |
| **Missing weekly letter** | Head of School letter publishes ~9:00 AM on Fridays | If checking on Friday before 9:00 AM, note that the week's letter is pending release |
| **Toddle dynamic canvas/image** | Weekly newsletter uploaded as an image/flyer instead of text | Download the image asset and use vision multimodal inspection to transcribe sections |
| **Duplicate task alerts** | No state caching | Always check `~/.gemini/antigravity/duchesne_state.json` before generating tasks |
| **Menu unavailable** | Nutrislice has not published the upcoming week yet | Check if current week's dates are selected; fall back to general schedule |
