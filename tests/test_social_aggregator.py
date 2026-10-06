import unittest
from scripts.social_aggregator import (
    REGISTERED_SOCIAL_CHANNELS,
    SocialPost,
    UnifiedSocialStory,
    normalize_caption,
    calculate_token_jaccard,
    deduplicate_posts,
    format_social_digest
)

class TestSocialAggregator(unittest.TestCase):
    def test_registered_channels_count(self):
        self.assertEqual(len(REGISTERED_SOCIAL_CHANNELS), 12)
        expected_channels = [
            "instagram_main", "instagram_athletics", "instagram_dance",
            "instagram_arts", "instagram_upper", "instagram_admissions",
            "instagram_alumnae", "linkedin_main", "facebook_main",
            "facebook_athletics", "facebook_alumnae", "youtube_main"
        ]
        for ch in expected_channels:
            self.assertIn(ch, REGISTERED_SOCIAL_CHANNELS)
            self.assertIn("name", REGISTERED_SOCIAL_CHANNELS[ch])
            self.assertIn("url", REGISTERED_SOCIAL_CHANNELS[ch])

    def test_normalize_caption(self):
        raw = "Varsity Volleyball sweeps Episcopal! 🏐 #chargers #duchesnehouston https://bit.ly/123"
        normalized = normalize_caption(raw)
        self.assertNotIn("https://", normalized)
        self.assertNotIn("#chargers", normalized)
        self.assertIn("varsity volleyball sweeps episcopal", normalized)

    def test_calculate_token_jaccard(self):
        text_a = "Varsity Volleyball sweeps Episcopal in 3 sets! Great job Chargers!"
        text_b = "Varsity Volleyball sweeps Episcopal in 3 sets! Great win Chargers!"
        sim = calculate_token_jaccard(text_a, text_b)
        self.assertGreater(sim, 0.7)
        self.assertLessEqual(sim, 1.0)

        # Disjoint text
        text_c = "Completely unrelated school drama play announcement tonight"
        sim_low = calculate_token_jaccard(text_a, text_c)
        self.assertLess(sim_low, 0.2)

        # Empty strings
        self.assertEqual(calculate_token_jaccard("", ""), 0.0)
        self.assertEqual(calculate_token_jaccard(text_a, ""), 0.0)

    def test_deduplicate_cross_posted_posts(self):
        post_ig = SocialPost(
            channel="instagram",
            channel_name="Instagram (@duchesneathletics)",
            url="https://instagram.com/p/1",
            caption="Varsity Volleyball sweeps Episcopal in 3 sets! Great job Chargers! #chargers",
            timestamp="2026-10-04T18:00:00Z"
        )
        post_fb = SocialPost(
            channel="facebook",
            channel_name="Facebook",
            url="https://facebook.com/posts/1",
            caption="Varsity Volleyball sweeps Episcopal in 3 sets! Great job Chargers!",
            timestamp="2026-10-04T18:05:00Z"
        )
        stories = deduplicate_posts([post_ig, post_fb], similarity_threshold=0.70)
        self.assertEqual(len(stories), 1)
        self.assertIn("Instagram (@duchesneathletics)", stories[0].source_links)
        self.assertIn("Facebook", stories[0].source_links)
        self.assertEqual(stories[0].timestamp, "2026-10-04")

    def test_deduplicate_distinct_posts(self):
        post1 = SocialPost(
            channel="instagram",
            channel_name="Instagram (@duchesnehouston)",
            url="https://instagram.com/p/1",
            caption="Welcome back students for a fantastic fall semester!",
            timestamp="2026-10-01T08:00:00Z"
        )
        post2 = SocialPost(
            channel="youtube",
            channel_name="YouTube",
            url="https://youtube.com/watch?v=1",
            caption="Watch our Upper School Choir performance from the fall concert.",
            timestamp="2026-10-02T10:00:00Z"
        )
        stories = deduplicate_posts([post1, post2])
        self.assertEqual(len(stories), 2)
        self.assertEqual(len(stories[0].source_links), 1)
        self.assertEqual(len(stories[1].source_links), 1)

    def test_deduplicate_empty_list(self):
        stories = deduplicate_posts([])
        self.assertEqual(stories, [])

    def test_format_social_digest(self):
        story = UnifiedSocialStory(
            story_id="s1",
            headline="Varsity Volleyball Sweeps Episcopal",
            summary="Decisive 3-0 victory at home.",
            timestamp="2026-10-04",
            source_links={"Instagram (@duchesneathletics)": "https://ig...", "Facebook": "https://fb..."}
        )
        digest = format_social_digest([story])
        self.assertIn("Varsity Volleyball", digest)
        self.assertIn("Instagram (@duchesneathletics)", digest)
        self.assertIn("Facebook", digest)

    def test_format_social_digest_empty(self):
        digest = format_social_digest([])
        self.assertIn("No new social updates this period", digest)

if __name__ == "__main__":
    unittest.main()
