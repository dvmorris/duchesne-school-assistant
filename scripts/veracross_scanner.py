#!/usr/bin/env python3
"""
Duchesne Veracross Multi-Division Scanner CLI Entrypoint
Coordinates profile loading, communication audit, message digest, calendar subscriptions,
and multi-division announcement synthesis.
"""

import argparse
import sys
import os
import json
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

DEFAULT_STATE_PATH = os.path.expanduser("~/.gemini/antigravity/duchesne_state.json")

def run_scanner(
    profile_path: Optional[str] = None,
    action: str = "full-scan",
    output: Optional[str] = None,
    state_path: Optional[str] = None,
    print_output: bool = True
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

    comm = audit_communication_settings({"faculty_messages_email": True, "division_announcements_email": True})
    digest = synthesize_family_digest(profile, items, comm, [], {})

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
        choices=["full-scan", "audit-comm", "messages", "calendars", "digest"],
        default="full-scan",
        help="Action to perform (default: full-scan)"
    )
    parser.add_argument("--output", help="Output file path (defaults to stdout)")

    args = parser.parse_args(argv)
    run_scanner(
        profile_path=args.profile,
        action=args.action,
        output=args.output,
        state_path=args.state,
        print_output=True
    )

if __name__ == "__main__":
    main()
