#!/usr/bin/env python3
"""
Duchesne School Assistant Helper Script
Manages state tracking, persistent browser profile setup, and portal checks.
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

DEFAULT_PROFILE_DIR = Path.home() / ".gemini" / "antigravity" / "browser_profiles" / "duchesne"
STATE_FILE = Path.home() / ".gemini" / "antigravity" / "duchesne_state.json"
CHROME_APP = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

VERACROSS_PARENT_URL = "https://portals.veracross.com/duchesne/parent"
VERACROSS_LS_URL = "https://portals.veracross.com/duchesne/parent/pages/ls-page"
TODDLE_URL = "https://web.toddleapp.com/platform/116643011487614044/courses"
NUTRISLICE_URL = "https://duchesne.nutrislice.com/menu/lower-school/lunch"

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_checked": None,
        "processed_announcement_ids": [],
        "processed_newsletters": [],
        "tasks": []
    }

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def launch_browser_for_auth(url=VERACROSS_PARENT_URL):
    """Launches Google Chrome with the dedicated Duchesne profile so the user can log in."""
    DEFAULT_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        CHROME_APP,
        f"--user-data-dir={DEFAULT_PROFILE_DIR}",
        "--remote-debugging-port=9222",
        url
    ]
    print(f"Launching Chrome with persistent profile: {DEFAULT_PROFILE_DIR}")
    print("Log into Veracross or Toddle via Google SSO / your credentials.")
    subprocess.Popen(cmd)

def check_status():
    state = load_state()
    print("=== Duchesne Assistant State ===")
    print(f"Profile directory: {DEFAULT_PROFILE_DIR} (Exists: {DEFAULT_PROFILE_DIR.exists()})")
    print(f"State file: {STATE_FILE}")
    print(f"Last checked: {state.get('last_checked', 'Never')}")
    print(f"Processed announcements: {len(state.get('processed_announcement_ids', []))}")
    print(f"Processed newsletters: {len(state.get('processed_newsletters', []))}")

def main():
    parser = argparse.ArgumentParser(description="Duchesne School Assistant automation helper")
    parser.add_argument("--login", action="store_true", help="Launch Chrome with persistent profile to sign into portals")
    parser.add_argument("--url", default=VERACROSS_PARENT_URL, help="URL to open for login")
    parser.add_argument("--status", action="store_true", help="Check local state and profile status")
    args = parser.parse_args()

    if args.login:
        launch_browser_for_auth(args.url)
    elif args.status:
        check_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
