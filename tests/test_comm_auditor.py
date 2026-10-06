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
        self.assertTrue(any("🔧 How to fix:" in w for w in result.critical_warnings))
        self.assertTrue(any("https://portals.veracross.com/duchesne/parent" in w for w in result.critical_warnings))
        self.assertTrue(any("Manage School Communication" in w for w in result.critical_warnings))
        self.assertTrue(any('Turn ON "Send an email copy"' in w for w in result.critical_warnings))

    def test_audit_passes_when_all_enabled(self):
        settings = {
            "faculty_messages_email": True,
            "division_announcements_email": True,
            "all_school_announcements_email": True
        }
        result = audit_communication_settings(settings)
        self.assertTrue(result.is_healthy)
        self.assertEqual(len(result.critical_warnings), 0)

    def test_audit_flags_disabled_division_announcements(self):
        settings = {
            "faculty_messages_email": True,
            "division_announcements_email": False,
            "all_school_announcements_email": True
        }
        result = audit_communication_settings(settings)
        self.assertFalse(result.is_healthy)
        self.assertTrue(any("Division Newsletters" in w for w in result.critical_warnings))

    def test_audit_records_advisory_for_all_school_announcements(self):
        settings = {
            "faculty_messages_email": True,
            "division_announcements_email": True,
            "all_school_announcements_email": False
        }
        result = audit_communication_settings(settings)
        self.assertTrue(result.is_healthy)
        self.assertEqual(len(result.critical_warnings), 0)
        self.assertTrue(any("School-wide announcements" in n for n in result.advisory_notes))

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

    def test_parse_communication_html_with_all_school(self):
        sample_html = """
        <div class="pref-row">
            <span class="label">Faculty Messages</span>
            <input type="checkbox" name="faculty_pref" checked="checked" />
        </div>
        <div class="pref-row">
            <span class="label">Division Announcements</span>
            <input type="checkbox" name="division_pref" />
        </div>
        <div class="pref-row">
            <span class="label">All-School Announcements</span>
            <input type="checkbox" name="all_school_pref" checked="checked" />
        </div>
        """
        parsed = parse_communication_html(sample_html)
        self.assertTrue(parsed.get("faculty_messages_email", False))
        self.assertFalse(parsed.get("division_announcements_email", True))
        self.assertTrue(parsed.get("all_school_announcements_email", False))

if __name__ == "__main__":
    unittest.main()
