import unittest
from datetime import datetime, timedelta, timezone
from scripts.message_digest import (
    VeracrossMessage,
    parse_messages,
    format_messages_digest,
    parse_iso_or_fallback
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

    def test_format_messages_digest_empty(self):
        output = format_messages_digest([])
        self.assertEqual(output, "No new Veracross messages in the last 14 days.")

    def test_parse_messages_action_detection(self):
        now = datetime.now(timezone.utc)
        recent = now.isoformat()
        raw_messages = [
            {
                "id": "m1",
                "sender": "Admin",
                "subject": "RSVP for Gala",
                "timestamp": recent,
                "body": "Join us for an evening of celebration.",
            },
            {
                "id": "m2",
                "sender": "Nurse",
                "subject": "General Health Notice",
                "timestamp": recent,
                "body": "Seasonal flu trends update.",
            }
        ]
        parsed = parse_messages(raw_messages, max_age_days=14)
        self.assertEqual(len(parsed), 2)
        self.assertTrue(parsed[0].is_action_needed)
        self.assertFalse(parsed[1].is_action_needed)

    def test_parse_messages_json_string(self):
        now = datetime.now(timezone.utc)
        recent = now.isoformat()
        raw_json = f"""[
            {{
                "id": "json_01",
                "sender": "Athletics Office",
                "subject": "Uniform Return Deadline",
                "timestamp": "{recent}",
                "body": "Submit clean jerseys by Friday."
            }}
        ]"""
        parsed = parse_messages(raw_json, max_age_days=14)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].id, "json_01")
        self.assertTrue(parsed[0].is_action_needed)

    def test_parse_messages_html_string(self):
        now = datetime.now(timezone.utc)
        recent = now.isoformat()
        html = f"""
        <div class="message" data-id="html_01" data-delivery-type="portal_only">
            <span class="sender">Music Dept</span>
            <span class="subject">Concert Permission Form</span>
            <span class="date">{recent}</span>
            <div class="body">Please submit the permission slip by Monday.</div>
        </div>
        """
        parsed = parse_messages(html, max_age_days=14)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].id, "html_01")
        self.assertEqual(parsed[0].sender, "Music Dept")
        self.assertEqual(parsed[0].subject, "Concert Permission Form")
        self.assertTrue(parsed[0].is_action_needed)

    def test_parse_messages_fallback_defaults(self):
        raw = [{}]
        parsed = parse_messages(raw, max_age_days=14)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].sender, "Duchesne Faculty")
        self.assertEqual(parsed[0].subject, "No Subject")
        self.assertEqual(parsed[0].snippet, "")
        self.assertFalse(parsed[0].is_action_needed)
        self.assertEqual(parsed[0].delivery_type, "portal_only")

    def test_parse_iso_or_fallback_timezone_aware(self):
        # Naive datetime string
        dt_naive = parse_iso_or_fallback("2026-10-05T14:00:00")
        self.assertIsNotNone(dt_naive.tzinfo)
        self.assertEqual(dt_naive.tzinfo, timezone.utc)
        self.assertEqual(dt_naive.year, 2026)
        self.assertEqual(dt_naive.month, 10)
        self.assertEqual(dt_naive.day, 5)
        self.assertEqual(dt_naive.hour, 14)

        # UTC with 'Z'
        dt_utc = parse_iso_or_fallback("2026-10-05T14:00:00Z")
        self.assertIsNotNone(dt_utc.tzinfo)
        self.assertEqual(dt_utc.tzinfo, timezone.utc)

        # Invalid/empty fallback
        dt_invalid = parse_iso_or_fallback("not-a-timestamp")
        self.assertIsNotNone(dt_invalid.tzinfo)
        self.assertEqual(dt_invalid.tzinfo, timezone.utc)

    def test_parse_messages_naive_timestamp(self):
        # Ensure comparison against cutoff does not raise TypeError: can't compare offset-naive and offset-aware datetimes
        now = datetime.now(timezone.utc)
        naive_recent = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        raw = [{
            "id": "naive_01",
            "sender": "Teacher",
            "subject": "Naive Timestamp Subject",
            "timestamp": naive_recent,
            "body": "Test message body."
        }]
        parsed = parse_messages(raw, max_age_days=14)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].id, "naive_01")


if __name__ == "__main__":
    unittest.main()
