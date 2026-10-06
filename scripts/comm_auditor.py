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
    """Parse HTML containing Veracross communication preference settings."""
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
        else:
            all_input = re.search(r'<input[^>]+name="[^"]*all[_-]?school[^"]*"[^>]*>', html_content, re.IGNORECASE)
            if all_input:
                settings["all_school_announcements_email"] = "checked" in all_input.group(0).lower()

    return settings

def audit_communication_settings(settings_data: Dict[str, bool]) -> CommunicationAuditResult:
    """Audit communication settings dictionary and produce warnings/advisories."""
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
