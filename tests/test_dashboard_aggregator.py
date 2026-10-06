import unittest
from scripts.profile_manager import ChildProfile, FamilyProfile
from scripts.comm_auditor import CommunicationAuditResult
from scripts.message_digest import VeracrossMessage
from scripts.dashboard_aggregator import (
    DashboardItem,
    synthesize_family_digest,
    parse_dashboard_items,
    format_grade
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
        self.assertIn("Urgent Deadlines & Action Items", digest)
        self.assertIn("Subscribe to Duchesne Calendars", digest)

    def test_synthesize_family_digest_unhealthy_comm(self):
        c1 = ChildProfile(first_name="Clara", last_name="Davis", division="lower_school", grade="PK4")
        profile = FamilyProfile(family_id="123", children=[c1])
        items = []
        comm = CommunicationAuditResult(
            is_healthy=False,
            critical_warnings=["Email notifications disabled for faculty messages."],
            advisory_notes=["School-wide announcements set to portal-only."]
        )

        digest = synthesize_family_digest(profile, items, comm)
        self.assertIn("⚠️ Communication Settings Status", digest)
        self.assertIn("Email notifications disabled for faculty messages.", digest)
        self.assertIn("School-wide announcements set to portal-only.", digest)
        self.assertIn("*(No active announcements for this division today)*", digest)

    def test_synthesize_family_digest_with_messages(self):
        c1 = ChildProfile(first_name="Clara", last_name="Davis", division="lower_school", grade="PK4")
        profile = FamilyProfile(family_id="123", children=[c1])
        items = []
        messages = [
            VeracrossMessage(
                id="msg1",
                sender="Coach Taylor",
                subject="Volleyball Practice Schedule",
                timestamp="2026-10-05T10:00:00Z",
                snippet="Please check the schedule.",
                is_action_needed=True
            )
        ]

        digest = synthesize_family_digest(profile, items, messages=messages)
        self.assertIn("Recent Veracross Messages", digest)
        self.assertIn("Coach Taylor", digest)
        self.assertIn("[Action Needed]", digest)

    def test_synthesize_family_digest_no_urgent_items(self):
        c1 = ChildProfile(first_name="Clara", last_name="Davis", division="lower_school", grade="PK4")
        profile = FamilyProfile(family_id="123", children=[c1])
        items = [
            DashboardItem(id="item1", division="lower_school", category="Homeroom", title="Art Display", snippet="Paintings in hallway", date="2026-10-05", is_urgent=False)
        ]

        digest = synthesize_family_digest(profile, items)
        self.assertNotIn("Urgent Deadlines & Action Items", digest)
        self.assertIn("Art Display", digest)

    def test_parse_dashboard_items_from_dict(self):
        raw_dict = {
            "lower_school": [
                {"id": "ls1", "category": "News", "title": "Field Trip", "snippet": "Bring lunch", "date": "2026-10-07", "is_urgent": True}
            ],
            "all_school": [
                {"id": "as1", "category": "General", "title": "Holiday", "snippet": "No school Monday", "date": "2026-10-12"}
            ]
        }
        parsed = parse_dashboard_items(raw_dict)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0].id, "ls1")
        self.assertEqual(parsed[0].division, "lower_school")
        self.assertTrue(parsed[0].is_urgent)
        self.assertEqual(parsed[1].division, "all_school")
        self.assertFalse(parsed[1].is_urgent)

    def test_format_grade(self):
        self.assertEqual(format_grade("PK4"), "PK4")
        self.assertEqual(format_grade("K"), "K")
        self.assertEqual(format_grade("1"), "1st")
        self.assertEqual(format_grade("2"), "2nd")
        self.assertEqual(format_grade("3"), "3rd")
        self.assertEqual(format_grade("7"), "7th")
        self.assertEqual(format_grade("7th"), "7th")
        self.assertEqual(format_grade("11"), "11th")
        self.assertEqual(format_grade("12"), "12th")

if __name__ == "__main__":
    unittest.main()
