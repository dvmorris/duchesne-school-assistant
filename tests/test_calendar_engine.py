import unittest
from urllib.parse import unquote
from scripts.calendar_engine import (
    generate_apple_calendar_link,
    generate_google_calendar_link,
    generate_outlook_calendar_link,
    format_calendar_subscription_instructions,
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
            "All-School": "https://portals.veracross.com/duchesne/subscribe/school_token.ics",
        }
        output = format_calendar_subscription_instructions(feeds)
        self.assertIn("Apple Calendar", output)
        self.assertIn("Google Calendar", output)
        self.assertIn("fam_token.ics", output)

    def test_format_instructions_empty(self):
        output = format_calendar_subscription_instructions({})
        self.assertEqual(output, "No calendar subscription feeds available.")

    def test_link_generation_schemes(self):
        feed_http = "http://portals.veracross.com/duchesne/subscribe/test.ics"
        self.assertEqual(
            generate_apple_calendar_link(feed_http),
            "webcal://portals.veracross.com/duchesne/subscribe/test.ics",
        )

        feed_webcal = "webcal://portals.veracross.com/duchesne/subscribe/test.ics"
        self.assertEqual(
            generate_apple_calendar_link(feed_webcal),
            "webcal://portals.veracross.com/duchesne/subscribe/test.ics",
        )

        google_from_webcal = generate_google_calendar_link(feed_webcal)
        self.assertIn(
            "https://portals.veracross.com/duchesne/subscribe/test.ics",
            unquote(google_from_webcal),
        )


if __name__ == "__main__":
    unittest.main()
