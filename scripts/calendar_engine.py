"""Calendar feed subscription formatter for Duchesne School Assistant.

Generates platform-specific subscription URLs and instructions for Apple Calendar,
Google Calendar, and Outlook from Veracross calendar feeds.
"""

import urllib.parse
from typing import Dict


def generate_apple_calendar_link(feed_url: str) -> str:
    """Transform an http/https or raw calendar feed URL to a webcal:// scheme link."""
    cleaned = feed_url.strip()
    if cleaned.startswith("http://"):
        return "webcal://" + cleaned[7:]
    if cleaned.startswith("https://"):
        return "webcal://" + cleaned[8:]
    if cleaned.startswith("webcal://"):
        return cleaned
    return "webcal://" + cleaned


def generate_google_calendar_link(feed_url: str) -> str:
    """Generate a 1-click Google Calendar web subscription URL with the cid param."""
    cleaned = feed_url.strip()
    # Google Calendar expects https:// encoded in cid parameter
    if cleaned.startswith("webcal://"):
        cleaned = "https://" + cleaned[9:]
    encoded_url = urllib.parse.quote(cleaned, safe="")
    return f"https://calendar.google.com/calendar/r?cid={encoded_url}"


def generate_outlook_calendar_link(feed_url: str) -> str:
    """Generate an Outlook Calendar add-calendar web link."""
    return "https://outlook.office.com/calendar/addcalendar"


def format_calendar_subscription_instructions(feeds: Dict[str, str]) -> str:
    """Format markdown instructions with 1-click subscription links for given calendar feeds."""
    if not feeds:
        return "No calendar subscription feeds available."

    sections = [
        "### 📅 Subscribe to Duchesne Calendars",
        "Add school calendars directly to your phone and computer to keep student schedules and all-school events automatically synced.\n",
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
