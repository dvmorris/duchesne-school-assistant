# Duchesne School Assistant: Multi-Division Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the multi-division and multi-child Veracross foundation for the Duchesne School Assistant, enabling family profile auto-discovery, selective division dashboard scraping, communication preferences auditing, message digests, and 1-click calendar subscriptions.

**Architecture:** A modular Python engine with clear separation of responsibilities (`profile_manager.py`, `comm_auditor.py`, `message_digest.py`, `calendar_engine.py`, `dashboard_aggregator.py`, and unified entrypoint `veracross_scanner.py`). State is stored in `duchesne_profile.json` and `duchesne_state.json`. Supports both Automated Mode (live session inspection) and Assisted Mode (chat input normalization).

**Tech Stack:** Python 3 (standard libraries: `json`, `hashlib`, `urllib.parse`, `datetime`, `re`, `argparse`, `unittest`).

**Spec:** [2026-10-06-duchesne-multi-division-core-design.md](file://./docs/superpowers/specs/2026-10-06-duchesne-multi-division-core-design.md)

## Global Constraints
- Python 3 compatibility using standard library where possible to ensure zero-dependency execution across macOS and Linux.
- Support 1 to N children across Lower School (`lower_school` / `LS`), Middle School (`middle_school` / `MS`), and Upper School (`upper_school` / `US`).
- Default storage location: `~/.gemini/antigravity/duchesne_profile.json` and `~/.gemini/antigravity/duchesne_state.json`, configurable via environment variable or CLI flag `--profile-path` / `--state-path`.
- All calendar links must encode feed parameters accurately for Apple Calendar (`webcal://`), Google Calendar (`https://calendar.google.com/calendar/r?cid=...`), and Microsoft Outlook (`https://outlook.office.com/calendar/addcalendar`).
- No external unverified network calls in unit tests; all unit tests must use mocked DOM/HTML payloads or JSON fixtures.

---

### Task 1: Family Profile & Multi-Child Configuration Store

**Files:**
- Create: `./scripts/profile_manager.py`
- Test: `./tests/test_profile_manager.py`

**Interfaces:**
- Consumes: JSON string or dictionary representation of family profiles.
- Produces:
  - `class ChildProfile(first_name, last_name, division, grade, homeroom_advisor, student_id, lms, toddle_class_id)`
  - `class FamilyProfile(family_id, children, active_dashboards, preferences)`
  - `save_profile(profile: FamilyProfile, filepath: str) -> None`
  - `load_profile(filepath: str) -> FamilyProfile`
  - `infer_dashboards_for_divisions(divisions: list[str], preferences: dict) -> list[str]`

- [ ] **Step 1: Write the failing test**

```python
import unittest
import os
import json
import tempfile
from scripts.profile_manager import (
    ChildProfile,
    FamilyProfile,
    save_profile,
    load_profile,
    infer_dashboards_for_divisions
)

class TestProfileManager(unittest.TestCase):
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
            self.assertEqual(loaded.children[1].grade, "7")
            self.assertEqual(loaded.children[1].division, "middle_school")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest ./tests/test_profile_manager.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.profile_manager'`

- [ ] **Step 3: Write minimal implementation in `scripts/profile_manager.py`**

```python
import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

DIVISION_MAP = {
    "pk3": "lower_school", "pk4": "lower_school", "k": "lower_school", "kindergarten": "lower_school",
    "1": "lower_school", "2": "lower_school", "3": "lower_school", "4": "lower_school",
    "ls": "lower_school", "lower": "lower_school", "lower_school": "lower_school",
    "5": "middle_school", "6": "middle_school", "7": "middle_school", "8": "middle_school",
    "ms": "middle_school", "middle": "middle_school", "middle_school": "middle_school",
    "9": "upper_school", "10": "upper_school", "11": "upper_school", "12": "upper_school",
    "us": "upper_school", "upper": "upper_school", "upper_school": "upper_school"
}

@dataclass
class ChildProfile:
    first_name: str
    last_name: str
    division: str
    grade: str
    homeroom_advisor: str = ""
    student_id: str = ""
    lms: str = "toddle"
    toddle_class_id: Optional[str] = None

@dataclass
class FamilyProfile:
    family_id: str = ""
    children: List[ChildProfile] = field(default_factory=list)
    active_dashboards: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=lambda: {
        "include_lunch_menus": True,
        "include_athletics": True,
        "include_fine_arts": True,
        "auto_audit_communications": True
    })

def normalize_division(grade_or_div: str) -> str:
    cleaned = grade_or_div.strip().lower()
    return DIVISION_MAP.get(cleaned, "lower_school")

def infer_dashboards_for_divisions(divisions: List[str], preferences: Optional[Dict[str, Any]] = None) -> List[str]:
    prefs = preferences or {}
    dashboards = ["all_school", "parent_association"]
    norm_divisions = {normalize_division(d) for d in divisions}

    for div in norm_divisions:
        if div not in dashboards:
            dashboards.append(div)

    if prefs.get("include_fine_arts", True) and "fine_arts" not in dashboards:
        dashboards.append("fine_arts")
    if prefs.get("include_athletics", True) and "athletics" not in dashboards:
        dashboards.append("athletics")
    if prefs.get("include_extended_programs", False) and "extended_programs" not in dashboards:
        dashboards.append("extended_programs")

    return dashboards

def save_profile(profile: FamilyProfile, filepath: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    data = asdict(profile)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_profile(filepath: str) -> FamilyProfile:
    if not os.path.exists(filepath):
        return FamilyProfile()
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    children = [ChildProfile(**c) for c in data.get("children", [])]
    return FamilyProfile(
        family_id=data.get("family_id", ""),
        children=children,
        active_dashboards=data.get("active_dashboards", []),
        preferences=data.get("preferences", {})
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest tests/test_profile_manager.py`
Expected: `Ran 2 tests in 0.00Xs ... OK`

- [ ] **Step 5: Verify**
Ensure code is cleanly formatted and typed.

---

### Task 2: Veracross Communication Preferences Auditor

**Files:**
- Create: `./scripts/comm_auditor.py`
- Test: `./tests/test_comm_auditor.py`

**Interfaces:**
- Consumes: HTML string or dictionary of Veracross communication settings.
- Produces:
  - `class CommunicationAuditResult(is_healthy: bool, critical_warnings: list[str], advisory_notes: list[str], settings: dict)`
  - `audit_communication_settings(settings_data: dict) -> CommunicationAuditResult`
  - `parse_communication_html(html_content: str) -> dict`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from scripts.comm_auditor import (
    audit_communication_settings,
    parse_communication_html,
    CommunicationAuditResult
)

class TestCommAuditor(unittest.TestCase):
    def test_audit_flags_disabled_faculty_messages(self):
        settings = {
            "faculty_messages_email": False,
            "division_announcements_email": True,
            "all_school_announcements_email": True
        }
        result = audit_communication_settings(settings)
        self.assertFalse(result.is_healthy)
        self.assertTrue(any("faculty and staff messages" in w for w in result.critical_warnings))

    def test_audit_passes_when_all_enabled(self):
        settings = {
            "faculty_messages_email": True,
            "division_announcements_email": True,
            "all_school_announcements_email": True
        }
        result = audit_communication_settings(settings)
        self.assertTrue(result.is_healthy)
        self.assertEqual(len(result.critical_warnings), 0)

    def test_parse_communication_html(self):
        sample_html = """
        <div class="pref-row">
            <span class="label">Direct Messages from Faculty/Staff</span>
            <input type="checkbox" name="pref_faculty" />
        </div>
        <div class="pref-row">
            <span class="label">Division Announcements</span>
            <input type="checkbox" name="pref_division" checked="checked" />
        </div>
        """
        parsed = parse_communication_html(sample_html)
        self.assertFalse(parsed.get("faculty_messages_email", True))
        self.assertTrue(parsed.get("division_announcements_email", False))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest tests/test_comm_auditor.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.comm_auditor'`

- [ ] **Step 3: Write minimal implementation in `scripts/comm_auditor.py`**

```python
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class CommunicationAuditResult:
    is_healthy: bool
    critical_warnings: List[str] = field(default_factory=list)
    advisory_notes: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)

def parse_communication_html(html_content: str) -> Dict[str, bool]:
    settings = {}
    
    # Check faculty/staff direct message toggle
    if "faculty" in html_content.lower() or "direct message" in html_content.lower():
        faculty_block = re.search(r'(?:faculty|direct message)[^<]*</span>\s*<input[^>]+>', html_content, re.IGNORECASE)
        if faculty_block:
            settings["faculty_messages_email"] = "checked" in faculty_block.group(0).lower()
        else:
            # Fallback regex for inputs with name/id
            faculty_input = re.search(r'<input[^>]+name="[^"]*faculty[^"]*"[^>]*>', html_content, re.IGNORECASE)
            if faculty_input:
                settings["faculty_messages_email"] = "checked" in faculty_input.group(0).lower()

    # Check division announcements
    if "division" in html_content.lower():
        div_block = re.search(r'division[^<]*</span>\s*<input[^>]+>', html_content, re.IGNORECASE)
        if div_block:
            settings["division_announcements_email"] = "checked" in div_block.group(0).lower()
        else:
            div_input = re.search(r'<input[^>]+name="[^"]*division[^"]*"[^>]*>', html_content, re.IGNORECASE)
            if div_input:
                settings["division_announcements_email"] = "checked" in div_input.group(0).lower()

    # Check all school
    if "all-school" in html_content.lower() or "all school" in html_content.lower():
        all_block = re.search(r'all[ -]school[^<]*</span>\s*<input[^>]+>', html_content, re.IGNORECASE)
        if all_block:
            settings["all_school_announcements_email"] = "checked" in all_block.group(0).lower()

    return settings

def audit_communication_settings(settings_data: Dict[str, bool]) -> CommunicationAuditResult:
    critical_warnings = []
    advisory_notes = []

    if not settings_data.get("faculty_messages_email", True):
        critical_warnings.append(
            "CRITICAL: Email notifications are turned OFF for direct faculty and staff messages. "
            "Messages sent by teachers will only appear inside the portal and will NOT be forwarded to your inbox."
        )

    if not settings_data.get("division_announcements_email", True):
        critical_warnings.append(
            "WARNING: Email notifications are turned OFF for Division Newsletters and Announcements."
        )

    if not settings_data.get("all_school_announcements_email", True):
        advisory_notes.append(
            "Advisory: School-wide announcements are set to portal-only."
        )

    is_healthy = len(critical_warnings) == 0
    return CommunicationAuditResult(
        is_healthy=is_healthy,
        critical_warnings=critical_warnings,
        advisory_notes=advisory_notes,
        settings=settings_data
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest tests/test_comm_auditor.py`
Expected: `Ran 3 tests in 0.00Xs ... OK`

---

### Task 3: Veracross Messages Digest Engine

**Files:**
- Create: `./scripts/message_digest.py`
- Test: `./tests/test_message_digest.py`

**Interfaces:**
- Consumes: Raw JSON or HTML representing Veracross portal messages.
- Produces:
  - `class VeracrossMessage(id, sender, subject, timestamp, snippet, is_action_needed, delivery_type)`
  - `parse_messages(raw_data: list[dict] | str, max_age_days: int = 14) -> list[VeracrossMessage]`
  - `format_messages_digest(messages: list[VeracrossMessage]) -> str`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from datetime import datetime, timedelta, timezone
from scripts.message_digest import (
    VeracrossMessage,
    parse_messages,
    format_messages_digest
)

class TestMessageDigest(unittest.TestCase):
    def test_parse_messages_filters_old_messages(self):
        now = datetime.now(timezone.utc)
        recent_date = (now - timedelta(days=2)).isoformat()
        old_date = (now - timedelta(days=20)).isoformat()

        raw_messages = [
            {
                "id": "msg_001",
                "sender": "Sample Faculty",
                "subject": "Library Book Reminder",
                "timestamp": recent_date,
                "body": "Please remember to return library books on Tuesday.",
                "delivery_type": "email_and_portal"
            },
            {
                "id": "msg_002",
                "sender": "Lower School Office",
                "subject": "Welcome Back Info",
                "timestamp": old_date,
                "body": "Information from August.",
                "delivery_type": "portal_only"
            }
        ]

        parsed = parse_messages(raw_messages, max_age_days=14)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].id, "msg_001")
        self.assertTrue(parsed[0].is_action_needed)

    def test_format_messages_digest(self):
        msg = VeracrossMessage(
            id="msg_001",
            sender="Sample Faculty",
            subject="Library Book Reminder",
            timestamp="2026-10-05T14:00:00Z",
            snippet="Please remember to return library books on Tuesday.",
            is_action_needed=True,
            delivery_type="email_and_portal"
        )
        output = format_messages_digest([msg])
        self.assertIn("Sample Faculty", output)
        self.assertIn("[Action Needed]", output)
        self.assertIn("Library Book Reminder", output)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest tests/test_message_digest.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.message_digest'`

- [ ] **Step 3: Write minimal implementation in `scripts/message_digest.py`**

```python
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Union, Dict, Any

ACTION_KEYWORDS = ["please", "remind", "bring", "submit", "return", "rsvp", "deadline", "form", "permission"]

@dataclass
class VeracrossMessage:
    id: str
    sender: str
    subject: str
    timestamp: str
    snippet: str
    is_action_needed: bool
    delivery_type: str = "portal_only"

def parse_iso_or_fallback(ts: str) -> datetime:
    try:
        clean_ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_ts)
    except Exception:
        return datetime.now(timezone.utc)

def parse_messages(raw_data: Union[List[Dict[str, Any]], str], max_age_days: int = 14) -> List[VeracrossMessage]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_age_days)
    results = []

    if isinstance(raw_data, list):
        for item in raw_data:
            ts_str = item.get("timestamp", "")
            dt = parse_iso_or_fallback(ts_str)
            if dt >= cutoff:
                body = item.get("body", "") or item.get("snippet", "")
                snippet = body[:200].strip()
                is_action = any(k in (item.get("subject", "") + " " + snippet).lower() for k in ACTION_KEYWORDS)
                results.append(VeracrossMessage(
                    id=str(item.get("id", "")),
                    sender=item.get("sender", "Duchesne Faculty"),
                    subject=item.get("subject", "No Subject"),
                    timestamp=ts_str,
                    snippet=snippet,
                    is_action_needed=is_action,
                    delivery_type=item.get("delivery_type", "portal_only")
                ))

    return results

def format_messages_digest(messages: List[VeracrossMessage]) -> str:
    if not messages:
        return "No new Veracross messages in the last 14 days."

    lines = ["### 📬 Recent Veracross Messages (Past 14 Days)"]
    for msg in messages:
        action_badge = "[Action Needed] " if msg.is_action_needed else ""
        date_str = msg.timestamp[:10] if len(msg.timestamp) >= 10 else msg.timestamp
        lines.append(f"- **{action_badge}{msg.sender}** — *{date_str}*")
        lines.append(f"  - **Subject:** {msg.subject}")
        lines.append(f"  - **Summary:** {msg.snippet}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest tests/test_message_digest.py`
Expected: `Ran 2 tests in 0.00Xs ... OK`

---

### Task 4: Calendar Feed Extractor & 1-Click Formatter

**Files:**
- Create: `./scripts/calendar_engine.py`
- Test: `./tests/test_calendar_engine.py`

**Interfaces:**
- Consumes: Raw calendar feed URL strings or dictionary of tokenized feeds.
- Produces:
  - `generate_apple_calendar_link(feed_url: str) -> str`
  - `generate_google_calendar_link(feed_url: str) -> str`
  - `generate_outlook_calendar_link(feed_url: str) -> str`
  - `format_calendar_subscription_instructions(feeds: dict[str, str]) -> str`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from urllib.parse import unquote
from scripts.calendar_engine import (
    generate_apple_calendar_link,
    generate_google_calendar_link,
    generate_outlook_calendar_link,
    format_calendar_subscription_instructions
)

class TestCalendarEngine(unittest.TestCase):
    def test_links_generation(self):
        feed = "https://portals.veracross.com/duchesne/subscribe/abc123token.ics"
        
        apple = generate_apple_calendar_link(feed)
        self.assertTrue(apple.startswith("webcal://"))
        self.assertIn("abc123token.ics", apple)

        google = generate_google_calendar_link(feed)
        self.assertTrue(google.startswith("https://calendar.google.com/calendar/r?cid="))
        self.assertIn("abc123token.ics", unquote(google))

        outlook = generate_outlook_calendar_link(feed)
        self.assertEqual(outlook, "https://outlook.office.com/calendar/addcalendar")

    def test_format_instructions(self):
        feeds = {
            "Family Schedule": "https://portals.veracross.com/duchesne/subscribe/fam_token.ics",
            "All-School": "https://portals.veracross.com/duchesne/subscribe/school_token.ics"
        }
        output = format_calendar_subscription_instructions(feeds)
        self.assertIn("Apple Calendar", output)
        self.assertIn("Google Calendar", output)
        self.assertIn("fam_token.ics", output)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest tests/test_calendar_engine.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.calendar_engine'`

- [ ] **Step 3: Write minimal implementation in `scripts/calendar_engine.py`**

```python
import urllib.parse
from typing import Dict

def generate_apple_calendar_link(feed_url: str) -> str:
    cleaned = feed_url.strip()
    if cleaned.startswith("http://"):
        return "webcal://" + cleaned[7:]
    if cleaned.startswith("https://"):
        return "webcal://" + cleaned[8:]
    if cleaned.startswith("webcal://"):
        return cleaned
    return "webcal://" + cleaned

def generate_google_calendar_link(feed_url: str) -> str:
    cleaned = feed_url.strip()
    # Google Calendar expects https:// encoded in cid parameter
    if cleaned.startswith("webcal://"):
        cleaned = "https://" + cleaned[9:]
    encoded_url = urllib.parse.quote(cleaned, safe="")
    return f"https://calendar.google.com/calendar/r?cid={encoded_url}"

def generate_outlook_calendar_link(feed_url: str) -> str:
    return "https://outlook.office.com/calendar/addcalendar"

def format_calendar_subscription_instructions(feeds: Dict[str, str]) -> str:
    if not feeds:
        return "No calendar subscription feeds available."

    sections = [
        "### 📅 Subscribe to Duchesne Calendars",
        "Add school calendars directly to your phone and computer to keep student schedules and all-school events automatically synced.\n"
    ]

    for name, url in feeds.items():
        apple_link = generate_apple_calendar_link(url)
        google_link = generate_google_calendar_link(url)
        outlook_link = generate_outlook_calendar_link(url)

        sections.append(f"#### 🗓️ {name}")
        sections.append(f"* **Feed URL:** `{url}`")
        sections.append(f"* [🍏 **1-Click Subscribe (Apple Calendar / Mac / iOS)**]({apple_link})")
        sections.append(f"* [📅 **1-Click Subscribe (Google Calendar Web)**]({google_link})")
        sections.append(f"* [✉️ **Add to Outlook Calendar**]({outlook_link})")
        sections.append(
            "  * *Outlook instructions:* Click the link above > Select **Subscribe from web** > Paste the Feed URL.\n"
        )

    return "\n".join(sections)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest tests/test_calendar_engine.py`
Expected: `Ran 2 tests in 0.00Xs ... OK`

---

### Task 5: Division Dashboard Aggregator & Synthesizer

**Files:**
- Create: `./scripts/dashboard_aggregator.py`
- Test: `./tests/test_dashboard_aggregator.py`

**Interfaces:**
- Consumes: Scanned dashboard data dict and `FamilyProfile`.
- Produces:
  - `class DashboardItem(id, division, category, title, snippet, date, is_urgent)`
  - `synthesize_family_digest(profile: FamilyProfile, dashboard_items: list[DashboardItem], comm_result: CommunicationAuditResult, messages: list[VeracrossMessage], calendar_feeds: dict[str, str]) -> str`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from scripts.profile_manager import ChildProfile, FamilyProfile
from scripts.comm_auditor import CommunicationAuditResult
from scripts.message_digest import VeracrossMessage
from scripts.dashboard_aggregator import (
    DashboardItem,
    synthesize_family_digest
)

class TestDashboardAggregator(unittest.TestCase):
    def test_synthesize_family_digest_multi_child(self):
        c1 = ChildProfile(first_name="Clara", last_name="Davis", division="lower_school", grade="PK4")
        c2 = ChildProfile(first_name="Jane", last_name="Davis", division="middle_school", grade="7")
        profile = FamilyProfile(family_id="123", children=[c1, c2])

        items = [
            DashboardItem(id="item1", division="all_school", category="Head Letter", title="Friday Welcome", snippet="Welcome back!", date="2026-10-02", is_urgent=False),
            DashboardItem(id="item2", division="lower_school", category="Homeroom", title="PK4 Library Day", snippet="Books due Tuesday", date="2026-10-05", is_urgent=True),
            DashboardItem(id="item3", division="middle_school", category="Advisory", title="7th Grade Retreat", snippet="Permission slips due", date="2026-10-06", is_urgent=True)
        ]

        comm = CommunicationAuditResult(is_healthy=True)
        messages = []
        feeds = {"All-School": "https://portals.veracross.com/duchesne/subscribe/token.ics"}

        digest = synthesize_family_digest(profile, items, comm, messages, feeds)
        self.assertIn("Clara — PK4", digest)
        self.assertIn("Jane — 7th", digest)
        self.assertIn("PK4 Library Day", digest)
        self.assertIn("7th Grade Retreat", digest)
        self.assertIn("Head Letter", digest)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest tests/test_dashboard_aggregator.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.dashboard_aggregator'`

- [ ] **Step 3: Write minimal implementation in `scripts/dashboard_aggregator.py`**

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from scripts.profile_manager import FamilyProfile
from scripts.comm_auditor import CommunicationAuditResult
from scripts.message_digest import VeracrossMessage, format_messages_digest
from scripts.calendar_engine import format_calendar_subscription_instructions

@dataclass
class DashboardItem:
    id: str
    division: str
    category: str
    title: str
    snippet: str
    date: str
    is_urgent: bool = False

def synthesize_family_digest(
    profile: FamilyProfile,
    dashboard_items: List[DashboardItem],
    comm_result: Optional[CommunicationAuditResult] = None,
    messages: Optional[List[VeracrossMessage]] = None,
    calendar_feeds: Optional[Dict[str, str]] = None
) -> str:
    lines = ["# 🏫 Duchesne Academy Updates\n"]

    # 1. Urgent Action Items
    urgent_items = [item for item in dashboard_items if item.is_urgent]
    if urgent_items:
        lines.append("### 🚨 Urgent Deadlines & Action Items")
        for item in urgent_items:
            lines.append(f"- [ ] **[{item.division.replace('_', ' ').title()}] {item.title}:** {item.snippet} ({item.date})")
        lines.append("")

    # 2. Communication Audit
    if comm_result:
        lines.append("### ⚠️ Communication Settings Status")
        if comm_result.is_healthy:
            lines.append("✅ Email notifications enabled for all faculty messages and division letters.\n")
        else:
            for warning in comm_result.critical_warnings:
                lines.append(f"> ⚠️ **{warning}**")
            lines.append("")

    # 3. Veracross Messages
    if messages:
        lines.append(format_messages_digest(messages))
        lines.append("")

    # 4. All-School Announcements
    all_school = [i for i in dashboard_items if i.division == "all_school"]
    if all_school:
        lines.append("### 🏛️ All-School Announcements")
        for item in all_school:
            lines.append(f"- **{item.category}: {item.title}** ({item.date}) — {item.snippet}")
        lines.append("")

    # 5. Grouped by Enrolled Child
    for child in profile.children:
        div_name = child.division
        child_items = [i for i in dashboard_items if i.division == div_name]
        lines.append(f"### 🎒 {child.division.replace('_', ' ').title()} ({child.first_name} — {child.grade})")
        if child_items:
            for item in child_items:
                lines.append(f"- **{item.title}**: {item.snippet}")
        else:
            lines.append("*(No active announcements for this division today)*")
        lines.append("")

    # 6. Calendar Subscriptions
    if calendar_feeds:
        lines.append(format_calendar_subscription_instructions(calendar_feeds))

    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest tests/test_dashboard_aggregator.py`
Expected: `Ran 1 test in 0.00Xs ... OK`

---

### Task 6: Unified Scanner Entrypoint & CLI

**Files:**
- Create: `./scripts/veracross_scanner.py`
- Modify: `./scripts/duchesne_check.py`
- Test: `./tests/test_veracross_scanner.py`

**Interfaces:**
- CLI flags:
  - `--profile`: JSON file path or interactive prompt.
  - `--action`: `[audit-comm, digest, calendars, full-scan]`
  - `--output`: markdown file or stdout.

- [ ] **Step 1: Write the failing test**

```python
import unittest
import subprocess
import sys

class TestVeracrossScannerCLI(unittest.TestCase):
    def test_cli_help(self):
        res = subprocess.run(
            [sys.executable, "./scripts/veracross_scanner.py", "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("--action", res.stdout)
        self.assertIn("--profile", res.stdout)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest ./tests/test_veracross_scanner.py`
Expected: FAIL with `file not found` or returncode non-zero.

- [ ] **Step 3: Implement `scripts/veracross_scanner.py`**

```python
#!/usr/bin/env python3
import argparse
import sys
import os
import json

from scripts.profile_manager import load_profile, save_profile, FamilyProfile, ChildProfile, infer_dashboards_for_divisions
from scripts.comm_auditor import audit_communication_settings, CommunicationAuditResult
from scripts.message_digest import parse_messages, VeracrossMessage
from scripts.calendar_engine import format_calendar_subscription_instructions
from scripts.dashboard_aggregator import DashboardItem, synthesize_family_digest

DEFAULT_PROFILE_PATH = os.path.expanduser("~/.gemini/antigravity/duchesne_profile.json")
DEFAULT_STATE_PATH = os.path.expanduser("~/.gemini/antigravity/duchesne_state.json")

def main():
    parser = argparse.ArgumentParser(description="Duchesne Veracross Multi-Division Scanner")
    parser.add_argument("--profile", default=DEFAULT_PROFILE_PATH, help="Path to duchesne_profile.json")
    parser.add_argument("--state", default=DEFAULT_STATE_PATH, help="Path to duchesne_state.json")
    parser.add_argument("--action", choices=["full-scan", "audit-comm", "messages", "calendars"], default="full-scan")
    parser.add_argument("--output", help="Output file path (defaults to stdout)")

    args = parser.parse_args()
    profile = load_profile(args.profile)

    # Fallback default if profile is empty
    if not profile.children:
        # Default fallback to Clara PK4
        profile.children = [ChildProfile(first_name="Clara", last_name="Davis", division="lower_school", grade="PK4", homeroom_advisor="Faculty, Sample")]
        profile.active_dashboards = infer_dashboards_for_divisions(["lower_school"])
        save_profile(profile, args.profile)

    if args.action == "audit-comm":
        sample_settings = {"faculty_messages_email": True, "division_announcements_email": True}
        res = audit_communication_settings(sample_settings)
        print("Healthy" if res.is_healthy else "Warning: Faculty email disabled")
        return

    if args.action == "calendars":
        sample_feeds = {
            "All-School Calendar": "https://portals.veracross.com/duchesne/subscribe/all_school.ics",
            "Family Schedule": "https://portals.veracross.com/duchesne/subscribe/family.ics"
        }
        print(format_calendar_subscription_instructions(sample_feeds))
        return

    # Full scan synthesis
    items = [
        DashboardItem(id="hos_letter", division="all_school", category="Head Letter", title="Head of School Friday Letter", snippet="Highlights from across the campus.", date="Friday", is_urgent=False)
    ]
    for child in profile.children:
        items.append(DashboardItem(
            id=f"{child.division}_update",
            division=child.division,
            category="Division Letter",
            title=f"Head of {child.division.replace('_', ' ').title()} Letter",
            snippet=f"Weekly updates for {child.grade}.",
            date="Friday",
            is_urgent=False
        ))

    comm = audit_communication_settings({"faculty_messages_email": True, "division_announcements_email": True})
    digest = synthesize_family_digest(profile, items, comm, [], {})

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(digest)
        print(f"Digest written to {args.output}")
    else:
        print(digest)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest tests/test_veracross_scanner.py`
Expected: `Ran 1 test in 0.00Xs ... OK`

---

### Task 7: Update `SKILL.md` Instructions for Multi-Division & Dual-Mode Usage

**Files:**
- Modify: `./SKILL.md`

- [ ] **Step 1: Update `SKILL.md` frontmatter & instructions**
  - Add documentation for all Veracross dashboards (LS, MS, US, Athletics, Fine Arts, PA).
  - Add instructions for `duchesne_profile.json` multi-child configuration.
  - Add instructions for "Manage School Communication" audit and warning banner.
  - Add instructions for calendar subscriptions (Apple, Google, Outlook 1-click links).
  - Add instructions for Assisted Mode (chat copy-paste prompts) alongside Automated Mode.

- [ ] **Step 2: Verify `SKILL.md` syntax and link integrity**
  - Validate with markdown inspection and run `python3 -m unittest discover tests`.
