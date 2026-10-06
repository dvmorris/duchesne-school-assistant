---
name: duchesne-school-assistant
description: Use when monitoring, retrieving, or organizing updates across Duchesne Academy of the Sacred Heart portals (Veracross All-School, Lower School, Middle School, Upper School, Athletics, Fine Arts, PA; Toddle LMS; Nutrislice lunch menus), auditing communication preferences, managing calendar subscriptions, or syncing school updates, newsletters, and photos to Google Workspace.
---

# Duchesne School Assistant

Universal assistant for families at **Duchesne Academy of the Sacred Heart** (Houston, TX). Automates monitoring, authentication, extraction, deduplication, and organization across all school divisions (Lower School PK3–4th, Middle School 5th–8th, Upper School 9th–12th), extracurriculars, internal messaging, calendar feeds, and Google Workspace integrations.

Supports **Dual-Mode Execution**:
- **Automated Mode:** Fully automated execution for local agents (Google Antigravity, Gemini Spark, Claude Code) with access to persistent browser profiles, scripts, and local tools.
- **Assisted Mode:** Interactive copy-paste guided execution for pure web chat agents (ChatGPT Plus, Claude.ai, Gemini Advanced) without local browser or terminal access.

---

## Quick Reference: Portals & Sources

| Portal / Resource | URL | Auth Required | Key Content |
|---|---|---|---|
| **Parent Dashboard** | `https://portals.veracross.com/duchesne/parent` | Yes (Veracross login / Google SSO) | Head of School Friday Letter (~9:00 AM Central), All-School Announcements, student switcher |
| **Lower School Dashboard** | `https://portals.veracross.com/duchesne/parent/pages/ls-page` | Yes (Veracross session) | Head of Lower School Letter, LS rolling calendar, uniform & liturgy dress days |
| **Middle School Dashboard** | `https://portals.veracross.com/duchesne/parent/pages/ms-page` | Yes (Veracross session) | Head of Middle School Letter, advisory topics, class trips, athletic tryouts, testing |
| **Upper School Dashboard** | `https://portals.veracross.com/duchesne/parent/pages/us-page` | Yes (Veracross session) | Head of Upper School Letter, college counseling, standardized testing, retreats |
| **Athletics Dashboard** | `https://portals.veracross.com/duchesne/parent/pages/athletics` | Yes (Veracross session) | Game schedules, team rosters, athletic forms, tryout dates |
| **Fine Arts Dashboard** | `https://portals.veracross.com/duchesne/parent/pages/fa-page` | Yes (Veracross session) | Performances, ticket releases, rehearsals, gallery exhibits |
| **Parent Association (PA)** | `https://portals.veracross.com/duchesne/parent/pages/pa-page` | Yes (Veracross session) | PA meetings, volunteer opportunities, Extravaganza galas, community events |
| **Extended Programs** | `https://portals.veracross.com/duchesne/parent/pages/ep-page` | Yes (Veracross session) | After-school care, enrichment programs, holiday camp registrations |
| **Veracross Messages** | `https://portals.veracross.com/duchesne/parent/messages` | Yes (Veracross session) | Direct faculty/staff messages, student progress notes (14-day rolling digest) |
| **Communication Preferences** | `https://portals.veracross.com/duchesne/parent/communication_preferences` | Yes (Veracross session) | Manage School Communication toggles (audit email forwarding status) |
| **Veracross Calendars** | `https://portals.veracross.com/duchesne/parent/calendar` | Yes (Veracross session) | Personalized family schedules & all-school subscription feeds (`webcal://` / `.ics`) |
| **Toddle LMS** | `https://web.toddleapp.com/platform/116643011487614044/courses` | Yes (Toddle login / Google SSO) | Homeroom weekly newsletter (Sophie's Space, Learning Focus, Reminders), Portfolio photos |
| **Lunch Menu** | `https://duchesne.nutrislice.com/menu/lower-school/lunch` | No (Public) | Daily & weekly Lower School lunch menus, allergens, nutritional details |
| **Instagram** | `https://www.instagram.com/duchesnehouston` | No (Public) | Campus event highlights, photos, sports recaps |

---

## Family Profile Configuration (`duchesne_profile.json`)

The assistant uses a structured family profile to dynamically adapt checks, dashboards, and reports to one or multiple enrolled children across different school divisions.

### File Location
- **Primary:** `~/.gemini/antigravity/duchesne_profile.json`
- **Fallback:** `./duchesne_profile.json` in the active workspace.
- **Helper module:** `scripts/profile_manager.py`

### Schema & Multi-Child Example
```json
{
  "family_id": "household_12345",
  "children": [
    {
      "student_id": "1001",
      "first_name": "Clara",
      "last_name": "Davis",
      "division": "lower_school",
      "grade": "PK4",
      "homeroom_advisor": "Faculty, Sample",
      "lms": "toddle",
      "toddle_class_id": "116643011487614044"
    },
    {
      "student_id": "1002",
      "first_name": "Clara",
      "last_name": "Davis",
      "division": "middle_school",
      "grade": "7",
      "homeroom_advisor": "Smith, Sarah",
      "lms": "veracross",
      "toddle_class_id": null
    }
  ],
  "active_dashboards": [
    "all_school",
    "parent_association",
    "lower_school",
    "middle_school",
    "fine_arts",
    "athletics"
  ],
  "preferences": {
    "include_lunch_menus": true,
    "include_athletics": true,
    "include_fine_arts": true,
    "include_extended_programs": false,
    "auto_audit_communications": true
  }
}
```

### Profile Discovery Logic
1. **Automated Discovery (Browser Session Active):**
   - Navigates to `https://portals.veracross.com/duchesne/parent`.
   - Inspects the "My Children" switcher (`select#student_switcher` or student card list).
   - Extracts student names, grades, advisor names, and division IDs.
   - Infers required division dashboards using `scripts/profile_manager.py:infer_dashboards_for_divisions()`.
   - Saves to `duchesne_profile.json` and displays a summary for one-click confirmation.
2. **Interactive Discovery (Assisted Mode Fallback):**
   - If no profile exists, prompt the parent:
     > *"Which grades and divisions do your children attend at Duchesne (e.g., PK4 in Lower School, 7th in Middle School)? Also, do you want to include Athletics, Fine Arts, or Extended Programs?"*
   - Normalize division names using `profile_manager.normalize_division(grade_or_div)`:
     - `pk3`, `pk4`, `k`, `1`–`4` → `lower_school`
     - `5`–`8` → `middle_school`
     - `9`–`12` → `upper_school`

---

## Dual-Mode Execution Guide

### Mode A: Automated Mode (Antigravity, Spark, Claude Code)

Use this mode when running in an agent environment with shell access, local Python runtime, and browser tools.

#### 1. Authentication & Persistent Chrome Profile
School portals (Veracross, Toddle) require parent authentication or Google SSO. **Never ask the user for raw passwords in chat.** Use a persistent Chrome profile:
```bash
# Launch Chrome with persistent profile for one-time login
python3 ~/.gemini/config/skills/duchesne-school-assistant/scripts/duchesne_check.py --login
```
Or directly:
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --user-data-dir="$HOME/.gemini/antigravity/browser_profiles/duchesne" \
  --remote-debugging-port=9222 \
  "https://portals.veracross.com/duchesne/parent"
```
Once logged in, cookies and session tokens persist across checks.

#### 2. Running Automated Veracross Checks
```bash
# Check assistant configuration, profile, and sync state
python3 ~/.gemini/config/skills/duchesne-school-assistant/scripts/duchesne_check.py --status

# Run full multi-division scan and generate synthesis
python3 ~/.gemini/config/skills/duchesne-school-assistant/scripts/veracross_scanner.py --action full-scan

# Audit communication preferences only
python3 ~/.gemini/config/skills/duchesne-school-assistant/scripts/veracross_scanner.py --action audit-comm

# Extract 14-day teacher messages digest
python3 ~/.gemini/config/skills/duchesne-school-assistant/scripts/veracross_scanner.py --action messages

# Format 1-click calendar subscription links
python3 ~/.gemini/config/skills/duchesne-school-assistant/scripts/veracross_scanner.py --action calendars
```

#### 3. Automated Weekly Sync (Lunch, Newsletters, Photos)
```bash
# Sync Lower School Nutrislice lunch menu to Google Calendar (10:55–11:25 AM Central)
node ~/.gemini/config/skills/duchesne-school-assistant/scripts/sync_lunch_to_calendar.js

# Download Toddle portfolio photos, embed EXIF metadata, and upload to Google Photos
node ~/.gemini/config/skills/duchesne-school-assistant/scripts/sync_toddle_photos.js
python3 ~/.gemini/config/skills/duchesne-school-assistant/scripts/tag_and_upload_photos.py
node ~/.gemini/config/skills/duchesne-school-assistant/scripts/upload_photos_browser.js

# Or run complete weekly batch
~/.gemini/config/skills/duchesne-school-assistant/scripts/run_weekly_sync.sh
```

---

### Mode B: Assisted Mode (ChatGPT, Claude.ai, Gemini Advanced)

Use this mode when running in a cloud web chat environment without a local shell or direct browser control.

#### Step 1: Initialize Family Profile
Prompt the user with this template:
> "To tailor your Duchesne Academy digest, please reply with:
> 1. Your children's names and current grades (e.g., Clara in PK4, Clara in 7th).
> 2. Any extracurricular areas to track (Athletics, Fine Arts, Extended Programs).
> 3. Whether you'd like an audit of your Veracross email delivery settings."

#### Step 2: Communication Preferences Audit Prompt
Guide the parent to verify their email notification settings:
> "Please open [Veracross Communication Preferences](https://portals.veracross.com/duchesne/parent/communication_preferences) (or click your name in the top right > **Manage School Communication**).
> Copy the text or screenshot on that page and paste it here.
> I will verify that your email forwarding toggles for faculty messages and division letters are active."

When the user pastes the content, evaluate the toggles using the rules in the Communication Preferences Audit section below. If direct faculty message forwarding is disabled, immediately display the **Critical Warning Banner**.

#### Step 3: Veracross Messages Digest Prompt
> "Please navigate to [Veracross Messages](https://portals.veracross.com/duchesne/parent/messages).
> Copy and paste the message list from the past 14 days into our chat.
> I will summarize all teacher communications, highlight action items/forms due, and verify delivery status."

#### Step 4: Division Announcements & Newsletters Prompt
> "Please open your division pages:
> - Lower School: `https://portals.veracross.com/duchesne/parent/pages/ls-page`
> - Middle School: `https://portals.veracross.com/duchesne/parent/pages/ms-page`
> - Upper School: `https://portals.veracross.com/duchesne/parent/pages/us-page`
> 
> Copy and paste the latest letters or announcement snippets here. For Toddle newsletters (PK3–4), paste the newsletter text or upload the weekly infographic image."

#### Step 5: Calendar Subscriptions Setup
> "To generate 1-click subscription links for your Apple Calendar, Google Calendar, or Outlook:
> Open [Veracross Calendar Subscriptions](https://portals.veracross.com/duchesne/parent/calendar) > click **Subscribe** > copy your calendar feed URL(s) (e.g. `https://portals.veracross.com/duchesne/subscribe/...ics`). Paste the links here and I will format one-click subscription links for your devices."

---

## Veracross Dashboard Coverage & Division Filtering

To prevent notification fatigue, the assistant filters dashboards strictly based on the family profile:

| Division / Dashboard | Route | Target Grade Levels | Key Content |
|---|---|---|---|
| **All-School** | `/parent` | All grades | Head of School Friday Letter (published ~9:00 AM Central on Fridays), campus liturgies, security/weather updates |
| **Parent Association** | `/parent/pages/pa-page` | All grades | PA general meetings, volunteer signups, Extravaganza auctions |
| **Lower School** | `/parent/pages/ls-page` | PK3, PK4, K, 1st–4th | Head of Lower School Letter, uniform guidelines, liturgical dress days, division calendar |
| **Middle School** | `/parent/pages/ms-page` | 5th–8th | Head of Middle School Letter, advisory themes, class trips, MS athletic tryouts, testing |
| **Upper School** | `/parent/pages/us-page` | 9th–12th | Head of Upper School Letter, college counseling, AP/standardized testing, retreats, graduation |
| **Athletics** | `/parent/pages/athletics` | 5th–12th | Middle & Upper School team schedules, rosters, physical evaluation forms, game locations |
| **Fine Arts** | `/parent/pages/fa-page` | All grades | Theater productions, choir concerts, band/orchestra rehearsals, art exhibitions |
| **Extended Programs** | `/parent/pages/ep-page` | PK3–8th | After-school care registration, enrichment classes, holiday camp schedules |

### Deduplication & State Tracking
The assistant maintains processed items in `~/.gemini/antigravity/duchesne_state.json`:
```json
{
  "last_checked": "2026-10-06T14:00:00Z",
  "processed_announcement_ids": [
    "hos_letter_20261002",
    "ls_head_letter_20261002",
    "ms_retreat_reminder_20261005"
  ],
  "processed_newsletters": [
    "toddle_mcevoy_20261005"
  ],
  "processed_photos": [
    "toddle_img_987654"
  ]
}
```
Items already marked as processed are excluded from urgent alerts unless they feature a pending deadline within the next 7 days.

---

## Communication Preferences Audit

Direct faculty and staff messages in Veracross are critical. If email forwarding is misconfigured in the portal, parents will never receive an email alert when a teacher or administrator reaches out.

### Audit Inspection Target
- **URL:** `https://portals.veracross.com/duchesne/parent/communication_preferences`
- **Portal Path:** Click parent name in top right > **Manage School Communication**
- **Underlying Module:** `scripts/comm_auditor.py`

### Inspection Rules & Critical Warning Banner
1. **Faculty/Staff Direct Messages:**
   - Evaluates whether "Send an email copy" or "Email" is checked for direct messages.
   - **CRITICAL WARNING:** If unchecked / disabled, MUST render the high-priority warning banner:

> ⚠️ **CRITICAL WARNING: Teacher Email Notifications Are Disabled!**
> Email notifications are currently turned **OFF** for direct messages from faculty and staff.
> Messages sent by teachers and advisors will only appear inside the Veracross portal—**you will NOT receive an email!**
> 
> **How to fix immediately:**
> 1. Go to [Veracross Communication Preferences](https://portals.veracross.com/duchesne/parent/communication_preferences) (or click your name in the top right > **Manage School Communication**).
> 2. Locate **Faculty and Staff Direct Messages**.
> 3. Turn **ON** "Send an email copy" / "Email notification".
> 4. Save your changes.

2. **Division Newsletters & Announcements:**
   - If disabled, flag with a warning:
   > ⚠️ **WARNING:** Email delivery is disabled for Division Newsletters and Announcements.
3. **All-School Announcements:**
   - If disabled, note as advisory:
   > ℹ️ *Advisory: School-wide announcements are configured for portal-only viewing.*

---

## Veracross Messages Digest

Extracts and digests messages received inside the portal over a rolling **14-day window**.

### Target Route & Extraction
- **URL:** `https://portals.veracross.com/duchesne/parent/messages`
- **Underlying Module:** `scripts/message_digest.py`

### Extracted Attributes per Message
- **Sender:** Teacher, advisor, or administrator name and department.
- **Date/Timestamp:** Date received.
- **Subject:** Message subject line.
- **Snippet:** 1–2 sentence summary of content.
- **Action Flag (`[Action Needed]`):** Automatically detected when text includes action keywords (`please`, `remind`, `bring`, `submit`, `return`, `rsvp`, `deadline`, `form`, `permission`).
- **Delivery Channel:** Explicitly note whether the message was `"Sent via Email"` or `"Portal Only"`.

---

## Universal Calendar Subscription Engine

Veracross provides personalized calendar feeds containing student schedules, division events, and school holidays. The assistant formats these into one-click native links.

### Target Route
- **URL:** `https://portals.veracross.com/duchesne/parent/calendar`
- **Underlying Module:** `scripts/calendar_engine.py`

### Supported Platforms & URL Formats

#### 1. Apple Calendar (macOS & iOS)
- Uses native `webcal://` scheme. Clicking opens the calendar subscription prompt directly:
  `webcal://portals.veracross.com/duchesne/subscribe/<token>.ics`

#### 2. Google Calendar (Android & Web)
- Formats direct 1-click web subscription link with URL-encoded target in the `cid` parameter:
  `https://calendar.google.com/calendar/r?cid=https%3A%2F%2Fportals.veracross.com%2Fduchesne%2Fsubscribe%2F<token>.ics`
- *Manual fallback:* In Google Calendar, click **+** next to "Other calendars" > **From URL** > paste feed link.

#### 3. Microsoft Outlook (Desktop & Web)
- Direct web link:
  `https://outlook.office.com/calendar/addcalendar`
- *Instructions:* Click link > Select **Subscribe from web** > Paste feed URL > Enter calendar name > Click **Import**.

---

## Toddle LMS Workflows (Lower School / Early Childhood)

For Lower School students (PK3–4th) enrolled in Toddle:

### Workflow 1: Extracting Weekly Homeroom Newsletters
1. Navigate to course: `https://web.toddleapp.com/platform/116643011487614044/courses`.
2. Locate homeroom: e.g. **PK4 Homeroom (PK4HR-01)**.
3. Switch to the **Home** tab to find the weekly newsletter graphic or PDF.
4. Extract the 3 core structured sections:
   - **Sophie's Space:** Prayers, Sacred Heart Goals (Goals I–V), monthly virtues/feelings, classroom helper duties.
   - **Learning Focus:** Number concepts, literacy (letters, sight words, phonics), science & social studies themes.
   - **Important Reminders:** Required items (e.g. 4x6 family photos), weekly library day, dress up/spirit days.
5. Check adjacent tabs:
   - **Class Announcements:** Teacher-posted schedule adjustments or special visitors.
   - **Portfolio:** Student work and class photos.

### Workflow 2: Toddle Photo Extraction & Google Photos Sync with EXIF
Automatically download class photos posted in the Toddle Portfolio tab, attach rich metadata, and upload to Google Photos:
1. **Locate Portfolio Media:**
   - In Toddle (`web.toddleapp.com`), switch to the **Portfolio** tab for the homeroom class.
   - Extract cards containing tagged student updates (e.g., `SubjectJournalCard` elements).
2. **Extract Rich Metadata:**
   - **Post Caption / Comments:** Teacher's note (e.g., *"B is for Banana Bread 🍌"*, *"Morning work stations 😊"*).
   - **Teacher Name:** e.g., `Faculty, Lower School`, `Faculty, Lower School`, `Faculty, Sample`.
   - **Student Tagged:** `Davis, Clara`.
   - **Date / Timestamp:** Exact post time (e.g., `2026-08-27 10:27:00`).
3. **Download & Stamp EXIF Metadata:**
   - Run `node scripts/sync_toddle_photos.js` to download full-resolution images.
   - Run `python3 scripts/tag_and_upload_photos.py` to embed:
     - **Image Description (EXIF 270):** Comments, teacher attribution, student name:
       ```text
       [Duchesne Academy - PK4] Pete the Cat with a special guest in guitar- Mr. Gallaher from upper school! | Teacher: Faculty, Sample | Student: Davis, Clara | Toddle: 2026:08:27 10:27:00
       ```
     - **Capture Timestamps (EXIF 36867 `DateTimeOriginal`, 36868 `DateTimeDigitized`, 306 `DateTime`):** Exact Toddle post time.
     - **Filesystem mtime:** Matched to original post timestamp so Google Photos chronologically orders them correctly.
4. **Google Photos & Drive Storage:**
   - **Google Photos (Zero-Config Browser Upload):** Run `node scripts/upload_photos_browser.js` to upload photos directly through the authenticated browser window using Chrome DevTools Protocol (CDP) file chooser interception (`DOM.setFileInputFiles`). No Google Cloud API keys or OAuth setup needed.
   - **Local & Drive Mirror:** Files are preserved in `~/Pictures/Duchesne PK4/` and mirrored in `~/Google Drive/Duchesne/Photos/`.
5. **Deduplication:**
   - Records processed image IDs in `~/.gemini/antigravity/duchesne_state.json` under `processed_photos`.

---

## Google Workspace Sync Workflows

### Google Drive Archival
1. **Target Folder:** Maintain or create the `Duchesne` folder in Google Drive.
2. **File Naming Standards:**
   - Newsletters: `Duchesne_Newsletter_YYYY-MM-DD_<Grade>.pdf` (or `.md`).
   - Photos: `Duchesne_Photo_YYYYMMDD_<ID>.jpg`.
3. **Execution:**
   - Antigravity / Shell: `python3 scripts/upload_to_gdrive.py --folder "Duchesne" --file <path>`.
   - Spark (MCP environment): Call `gdrive:upload` with parent folder ID.
4. **State Tracking:** Record uploaded file IDs in `duchesne_state.json`.

### Google Calendar & Google Tasks Sync
- **PK4 Lunch Menu Sync:**
  - Synchronizes weekly Nutrislice menus to Google Calendar at the PK4 lunch period (**10:55 AM – 11:25 AM Central**).
  - Run `node scripts/sync_lunch_to_calendar.js`.
  - Automatically generates `Duchesne_Lunch_Menu_YYYY-MM-DD.ics` and imports via Chrome CDP directly into Google Calendar.
  - Includes daily entrees, vegetarian alternate, sides, soups, and allergy warnings.
- **Calendar Events:**
  - Weekly recurring: Library Days, PE uniform days, Liturgy/Mass uniform days.
  - One-off events: Parent-teacher conferences, division performances, school holidays.
- **Tasks (Actionable Items):**
  - Extract supplies, photo submissions, permission slips, or book return deadlines.
  - Format title clearly: `[Duchesne <Division>] Return library books` or `[Duchesne <Grade>] Submit permission slip`.
  - Assign explicit due dates parsed from reminder text.

---

## Standard Multi-Division Output Report

When producing a daily or weekly synthesized report, format output using clear, consistent sections:

```markdown
# 🏫 Duchesne Academy Updates — [Date]

### 🚨 Urgent Deadlines & Action Items (All Children)
- [ ] **[All-School] Emergency Card Update:** Submit through Veracross Parent Portal (Due: 2026-10-15)
- [ ] **[Lower School - PK4] Library Books:** Return library bag and books for weekly check-out (Due: Tuesday)
- [ ] **[Middle School - 7th] Science Fair Proposal:** Submit signed topic sheet to Advisor (Due: Friday)

### ⚠️ Communication Settings Status
✅ Email notifications enabled for all faculty messages and division letters.
*(OR if misconfigured:)*
> ⚠️ **CRITICAL WARNING:** Email notifications are currently disabled for direct messages from teachers and staff. You will NOT receive emails when teachers contact you!
> **Fix:** In Veracross, click your name in the top right > **Manage School Communication** > turn ON **Send an email copy** for faculty messages.

### 📬 Recent Veracross Messages (Past 14 Days)
- **[Action Needed] Sample Faculty** — *2026-10-05*
  - **Subject:** Class Party Volunteer Signups
  - **Summary:** Sign up for fall celebration supplies by Wednesday.
  - **Delivery:** Sent via Email & Portal

### 🏛️ All-School Announcements
- **Head of School Friday Letter (Head of School):** Welcome back reflection and Sacred Heart Goal I focus.
- **Parent Association (PA):** Volunteer positions open for Extravaganza committee.

### 🎒 Lower School (Clara — PK4)
- **Head of Lower School Letter:** Blessing of the Animals recap; uniform reminders for cooler weather.
- **PK4 Homeroom Updates:**
  - *Sophie's Space:* Goal I (Personal and active faith in God); October virtue: Kindness.
  - *Learning Focus:* Letters P & Q, counting sets of 10, autumn leaves study.
  - *Reminders:* Bring 4x6 family photo; Library on Tuesday.

### 📚 Middle School (Clara — 7th)
- **Head of Middle School Letter:** Quarter 1 midterm feedback and student-led conferences preview.
- **Advisory & Academics:** Fall retreat registration open; bring athletic uniform on Wednesday.

### 🥗 Lower School Lunch Menu (Upcoming Days)
- **Monday:** Baked Chicken Tenders, Macaroni & Cheese, Steamed Broccoli (Veg: Black Bean Burger)
- **Tuesday:** Beef Tacos, Spanish Rice, Pinto Beans (Veg: Bean & Cheese Tacos)

### 📅 Calendar Subscriptions
#### 🗓️ All-School Calendar
* **Feed URL:** `https://portals.veracross.com/duchesne/subscribe/all_school.ics`
* [🍏 **1-Click Subscribe (Apple Calendar / Mac / iOS)**](webcal://portals.veracross.com/duchesne/subscribe/all_school.ics)
* [📅 **1-Click Subscribe (Google Calendar Web)**](https://calendar.google.com/calendar/r?cid=https%3A%2F%2Fportals.veracross.com%2Fduchesne%2Fsubscribe%2Fall_school.ics)
* [✉️ **Add to Outlook Calendar**](https://outlook.office.com/calendar/addcalendar)

### 🗄️ Archival & Sync Status
- Google Drive: Saved `Duchesne_Newsletter_2026-10-05_PK4.pdf`
- Google Calendar: Added 5 lunch menu events (10:55–11:25 AM)
- Google Photos: Synced 4 portfolio photos with EXIF date/caption stamps
```

---

## Common Mistakes & Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| **Auth redirect loop** | Expired session or stale cookies in persistent Chrome profile | Run `python3 scripts/duchesne_check.py --login` to launch interactive browser and complete SSO |
| **Missing Friday letter** | Checked before publication window | Head of School letter publishes ~9:00 AM Central on Fridays; check after 9:15 AM |
| **Toddle flyer is image/canvas** | Newsletter posted as Canva graphic or image file rather than text | Use multimodal vision inspection to transcribe text from image assets |
| **Faculty emails missed** | Portal forwarder toggle disabled in Veracross | Run communication audit (`--action audit-comm`) and follow the fix steps in the warning banner |
| **Google Calendar feed error** | Scheme prefix `webcal://` passed directly into Google `cid` param | Strip `webcal://` to `https://` before URL-encoding into `calendar.google.com/calendar/r?cid=...` (handled automatically by `scripts/calendar_engine.py`) |
| **Multi-division clutter** | Inactive division dashboards enabled in profile | Edit `~/.gemini/antigravity/duchesne_profile.json` to keep only enrolled child divisions in `active_dashboards` |
| **Duplicate task alerts** | Local state cache missing or not updated | Verify `~/.gemini/antigravity/duchesne_state.json` exists and is updated after each scan |
| **Nutrislice menu blank** | Next week's menu not yet published | Nutrislice typically posts upcoming menus on Friday afternoon; fall back to current week's remaining days |
