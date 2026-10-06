#!/usr/bin/env python3
"""
Duchesne Veracross Multi-Division Scanner CLI Entrypoint
Coordinates profile loading, communication audit, message digest, calendar subscriptions,
spirit store catalog, directory contacts, social media aggregation, and multi-division
announcement synthesis.
"""

import argparse
import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.profile_manager import (
    load_profile,
    save_profile,
    FamilyProfile,
    ChildProfile,
    infer_dashboards_for_divisions,
    DEFAULT_PROFILE_PATH
)
from scripts.comm_auditor import audit_communication_settings, CommunicationAuditResult
from scripts.message_digest import parse_messages, format_messages_digest, VeracrossMessage
from scripts.calendar_engine import format_calendar_subscription_instructions
from scripts.dashboard_aggregator import DashboardItem, synthesize_family_digest
from scripts.spirit_store_crawler import (
    parse_store_catalog,
    detect_new_and_featured,
    format_store_digest,
    StoreItem
)
from scripts.directory_exporter import (
    parse_directory_roster,
    generate_vcard_content,
    generate_google_contacts_csv,
    export_contacts,
    ParentContact
)
from scripts.social_aggregator import (
    REGISTERED_SOCIAL_CHANNELS,
    SocialPost,
    UnifiedSocialStory,
    deduplicate_posts,
    format_social_digest
)

DEFAULT_STATE_PATH = os.path.expanduser("~/.gemini/antigravity/duchesne_state.json")

SAMPLE_STORE_ITEMS = {
    "items": [
        {
            "id": "store_001",
            "name": "Navy Fleece Full-Zip Jacket",
            "price": "$48.00",
            "category": "Outerwear",
            "url": "/product/navy-fleece-jacket/1"
        },
        {
            "id": "store_002",
            "name": "Charger Spirit T-Shirt",
            "price": "$20.00",
            "category": "Apparel",
            "url": "/product/charger-spirit-tshirt/2"
        },
        {
            "id": "store_003",
            "name": "Plaid Uniform Hair Bow",
            "price": "$12.00",
            "category": "Accessories",
            "url": "/product/plaid-hair-bow/3"
        }
    ]
}

SAMPLE_ROSTER_ITEMS = [
    {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "phone": "(713) 555-0123",
        "child_name": "Clara Davis",
        "child_grade": "PK4",
        "address": "10202 Memorial Dr, Houston, TX 77024"
    },
    {
        "first_name": "Sophia",
        "last_name": "Johnson",
        "email": "sophia.j@example.com",
        "phone": "(713) 555-0199",
        "child_name": "Emma Johnson",
        "child_grade": "7",
        "address": "10202 Memorial Dr, Houston, TX 77024"
    }
]

SAMPLE_SOCIAL_POSTS = [
    SocialPost(
        channel="instagram_athletics",
        channel_name="Instagram (@duchesneathletics)",
        url="https://www.instagram.com/p/charger_volleyball_1",
        caption="Varsity Volleyball sweeps Episcopal in 3 sets! 🏐 Outstanding effort by all our Chargers! #duchesneathletics #chargers",
        timestamp="2026-10-05T18:30:00Z"
    ),
    SocialPost(
        channel="facebook_athletics",
        channel_name="Facebook (Athletics & Campus Life)",
        url="https://www.facebook.com/posts/charger_volleyball_fb1",
        caption="Varsity Volleyball sweeps Episcopal in 3 sets! Great effort by our Chargers! 🏐",
        timestamp="2026-10-05T18:35:00Z"
    ),
    SocialPost(
        channel="instagram_main",
        channel_name="Instagram (@duchesnehouston)",
        url="https://www.instagram.com/p/sacred_heart_traditions",
        caption="Celebrating Sacred Heart traditions across all divisions this week. ❤️ #duchesnehouston",
        timestamp="2026-10-04T12:00:00Z"
    )
]

def get_current_season(now: Optional[datetime] = None) -> str:
    current_month = (now or datetime.now()).month
    # Oct-Feb -> "fall" (Fall/Winter), Mar-May -> "spring", Jun-Sep -> "fall" (back-to-school)
    if current_month in (3, 4, 5):
        return "spring"
    return "fall"

def _normalize_grade(g: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]', '', g).lower()
    for _ in range(2):
        for suffix in ["grade", "th", "st", "nd", "rd"]:
            if s.endswith(suffix):
                s = s[:-len(suffix)]
    return s

def _matches_grade(child_grade: str, target_grade: str) -> bool:
    if not child_grade or not target_grade:
        return False
    cg = _normalize_grade(child_grade)
    tg = _normalize_grade(target_grade)
    return cg == tg

def format_contacts_digest(contacts: List[ParentContact], grade_filter: Optional[str] = None) -> str:
    header = "### 👥 Duchesne Parent Directory"
    if grade_filter:
        header += f" ({grade_filter})"
    lines = [header]
    if not contacts:
        lines.append("*(No contacts found)*")
    else:
        for c in contacts:
            grade_str = f" — {c.child_grade}" if c.child_grade else ""
            student_info = f" (Parent of {c.child_name}{grade_str})" if c.child_name else ""
            lines.append(f"\n* **{c.first_name} {c.last_name}**{student_info}")
            if c.email:
                lines.append(f"  - 📧 Email: {c.email}")
            if c.phone:
                lines.append(f"  - 📞 Phone: {c.phone}")
            if c.address:
                lines.append(f"  - 📍 Address: {c.address}")
    return "\n".join(lines)

def run_scanner(
    profile_path: Optional[str] = None,
    action: str = "full-scan",
    output: Optional[str] = None,
    state_path: Optional[str] = None,
    print_output: bool = True,
    grade: Optional[str] = None
) -> str:
    prof_path = profile_path or DEFAULT_PROFILE_PATH
    profile = load_profile(prof_path)

    # Fallback default if profile is empty
    if not profile.children:
        profile.children = [
            ChildProfile(
                first_name="Clara",
                last_name="Davis",
                division="lower_school",
                grade="PK4",
                homeroom_advisor="Faculty, Sample"
            )
        ]
        profile.active_dashboards = infer_dashboards_for_divisions(["lower_school"])
        save_profile(profile, prof_path)

    if action == "audit-comm":
        sample_settings = {"faculty_messages_email": True, "division_announcements_email": True}
        res = audit_communication_settings(sample_settings)
        out = "Healthy" if res.is_healthy else "Warning: Faculty email disabled"
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(out + "\n")
            if print_output:
                print(f"Output written to {output}")
        elif print_output:
            print(out)
        return out

    if action == "calendars":
        sample_feeds = {
            "All-School Calendar": "https://portals.veracross.com/duchesne/subscribe/all_school.ics",
            "Family Schedule": "https://portals.veracross.com/duchesne/subscribe/family.ics"
        }
        out = format_calendar_subscription_instructions(sample_feeds)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(out)
            if print_output:
                print(f"Output written to {output}")
        elif print_output:
            print(out)
        return out

    if action == "messages":
        sample_messages = [
            {
                "id": "msg_001",
                "sender": "Sample Faculty",
                "subject": "Weekly Class Update",
                "timestamp": "2026-10-05T10:00:00Z",
                "body": "Please remember to check your student folder.",
                "delivery_type": "email_and_portal"
            }
        ]
        parsed = parse_messages(sample_messages)
        out = format_messages_digest(parsed)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(out)
            if print_output:
                print(f"Output written to {output}")
        elif print_output:
            print(out)
        return out

    if action == "store":
        store_items = parse_store_catalog(SAMPLE_STORE_ITEMS)
        known_store_ids = []
        if state_path and os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    st = json.load(f)
                    known_store_ids = st.get("processed_store_item_ids", [])
            except Exception:
                pass
        new_arrivals, featured = detect_new_and_featured(store_items, known_ids=known_store_ids, season=get_current_season())
        out = format_store_digest(new_arrivals, featured)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(out + "\n")
            if print_output:
                print(f"Output written to {output}")
        elif print_output:
            print(out)
        return out

    if action == "contacts":
        contacts = parse_directory_roster(SAMPLE_ROSTER_ITEMS)
        if grade:
            contacts = [c for c in contacts if _matches_grade(c.child_grade, grade)]
        elif profile and profile.children:
            target_grades = [c.grade for c in profile.children if c.grade]
            if target_grades:
                contacts = [c for c in contacts if any(_matches_grade(c.child_grade, tg) for tg in target_grades)]

        out = format_contacts_digest(contacts, grade_filter=grade)
        if output:
            if output.endswith(".vcf"):
                with open(output, "w", encoding="utf-8") as f:
                    f.write(generate_vcard_content(contacts))
            elif output.endswith(".csv"):
                with open(output, "w", encoding="utf-8") as f:
                    f.write(generate_google_contacts_csv(contacts))
            else:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(out + "\n")
            if print_output:
                print(f"Output written to {output}")
        elif print_output:
            print(out)
        return out

    if action == "social":
        social_stories = deduplicate_posts(SAMPLE_SOCIAL_POSTS)
        out = format_social_digest(social_stories)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(out + "\n")
            if print_output:
                print(f"Output written to {output}")
        elif print_output:
            print(out)
        return out

    # Full scan synthesis (action in ("full-scan", "digest"))
    items = [
        DashboardItem(
            id="hos_letter",
            division="all_school",
            category="Head Letter",
            title="Head of School Friday Letter",
            snippet="Highlights from across the campus.",
            date="Friday",
            is_urgent=False
        )
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

    known_store_ids = []
    if state_path and os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                st = json.load(f)
                known_store_ids = st.get("processed_store_item_ids", [])
        except Exception:
            pass

    store_items = parse_store_catalog(SAMPLE_STORE_ITEMS)
    new_arrivals, featured = detect_new_and_featured(store_items, known_ids=known_store_ids, season=get_current_season())
    store_section = format_store_digest(new_arrivals, featured)

    social_stories = deduplicate_posts(SAMPLE_SOCIAL_POSTS)
    social_section = format_social_digest(social_stories)

    comm = audit_communication_settings({"faculty_messages_email": True, "division_announcements_email": True})
    digest = synthesize_family_digest(
        profile,
        items,
        comm,
        [],
        {},
        store_section=store_section,
        social_section=social_section
    )

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(digest)
        if print_output:
            print(f"Digest written to {output}")
    elif print_output:
        print(digest)

    return digest

def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description="Duchesne Veracross Multi-Division Scanner")
    parser.add_argument("--profile", default=DEFAULT_PROFILE_PATH, help="Path to duchesne_profile.json")
    parser.add_argument("--state", default=DEFAULT_STATE_PATH, help="Path to duchesne_state.json")
    parser.add_argument(
        "--action",
        choices=["full-scan", "audit-comm", "messages", "calendars", "digest", "store", "contacts", "social"],
        default="full-scan",
        help="Action to perform (default: full-scan)"
    )
    parser.add_argument("--output", help="Output file path (defaults to stdout)")
    parser.add_argument("--grade", help="Optional grade filter for directory contacts (e.g. PK4, 7)")

    args = parser.parse_args(argv)
    run_scanner(
        profile_path=args.profile,
        action=args.action,
        output=args.output,
        state_path=args.state,
        print_output=True,
        grade=args.grade
    )

if __name__ == "__main__":
    main()
