"""Division dashboard aggregator and family report synthesizer.

Consolidates family profile data, scanned division announcements,
communication preference audits, recent teacher messages, and calendar feeds
into a unified Markdown parent digest.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Any
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


def format_grade(grade: str) -> str:
    """Format grade string to ensure standard ordinal display for numeric grades."""
    grade_str = grade.strip()
    if grade_str.isdigit():
        n = int(grade_str)
        if 11 <= (n % 100) <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"
    return grade_str


def parse_dashboard_items(
    raw_data: Union[List[Union[Dict[str, Any], DashboardItem]], Dict[str, Any]]
) -> List[DashboardItem]:
    """Parse raw scanned dashboard data (grouped dictionary or list of dicts) into DashboardItem list."""
    items: List[DashboardItem] = []
    if isinstance(raw_data, dict):
        if "items" in raw_data and isinstance(raw_data["items"], list):
            return parse_dashboard_items(raw_data["items"])
        for div_key, div_items in raw_data.items():
            if isinstance(div_items, list):
                for entry in div_items:
                    if isinstance(entry, DashboardItem):
                        items.append(entry)
                    elif isinstance(entry, dict):
                        items.append(DashboardItem(
                            id=str(entry.get("id", "")),
                            division=str(entry.get("division", div_key)),
                            category=str(entry.get("category", "")),
                            title=str(entry.get("title", "")),
                            snippet=str(entry.get("snippet", "")),
                            date=str(entry.get("date", "")),
                            is_urgent=bool(entry.get("is_urgent", False))
                        ))
    elif isinstance(raw_data, list):
        for entry in raw_data:
            if isinstance(entry, DashboardItem):
                items.append(entry)
            elif isinstance(entry, dict):
                items.append(DashboardItem(
                    id=str(entry.get("id", "")),
                    division=str(entry.get("division", "all_school")),
                    category=str(entry.get("category", "")),
                    title=str(entry.get("title", "")),
                    snippet=str(entry.get("snippet", "")),
                    date=str(entry.get("date", "")),
                    is_urgent=bool(entry.get("is_urgent", False))
                ))
    return items


def synthesize_family_digest(
    profile: FamilyProfile,
    dashboard_items: List[DashboardItem],
    comm_result: Optional[CommunicationAuditResult] = None,
    messages: Optional[List[VeracrossMessage]] = None,
    calendar_feeds: Optional[Dict[str, str]] = None,
    store_section: Optional[str] = None,
    social_section: Optional[str] = None
) -> str:
    """Synthesize a complete multi-division family digest in Markdown format."""
    lines = ["# 🏫 Duchesne Academy Updates\n"]

    # 1. Urgent Action Items
    urgent_items = [item for item in dashboard_items if item.is_urgent]
    if urgent_items:
        lines.append("### 🚨 Urgent Deadlines & Action Items")
        for item in urgent_items:
            date_str = f" ({item.date})" if item.date else ""
            lines.append(f"- [ ] **[{item.division.replace('_', ' ').title()}] {item.title}:** {item.snippet}{date_str}")
        lines.append("")

    # 2. Communication Audit
    if comm_result:
        lines.append("### ⚠️ Communication Settings Status")
        if comm_result.is_healthy:
            lines.append("✅ Email notifications enabled for all faculty messages and division letters.\n")
        else:
            for warning in comm_result.critical_warnings:
                lines.append(f"> ⚠️ **{warning}**")
            for note in comm_result.advisory_notes:
                lines.append(f"> ℹ️ *{note}*")
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
            cat_prefix = f"{item.category}: " if item.category else ""
            date_str = f" ({item.date})" if item.date else ""
            lines.append(f"- **{cat_prefix}{item.title}**{date_str} — {item.snippet}")
        lines.append("")

    # 5. Grouped by Enrolled Child
    for child in profile.children:
        div_name = child.division
        child_items = [i for i in dashboard_items if i.division == div_name]
        grade_str = format_grade(child.grade)
        lines.append(f"### 🎒 {child.division.replace('_', ' ').title()} ({child.first_name} — {grade_str})")
        if child_items:
            for item in child_items:
                lines.append(f"- **{item.title}**: {item.snippet}")
        else:
            lines.append("*(No active announcements for this division today)*")
        lines.append("")

    # 6. Duchesne Spirit Store
    if store_section:
        lines.append(store_section)
        lines.append("")

    # 7. Social Media Highlights
    if social_section:
        lines.append(social_section)
        lines.append("")

    # 8. Calendar Subscriptions
    if calendar_feeds:
        lines.append(format_calendar_subscription_instructions(calendar_feeds))

    return "\n".join(lines)
