import re
from dataclasses import dataclass, field
from typing import List, Dict

REGISTERED_SOCIAL_CHANNELS = {
    "instagram_main": {"name": "Instagram (@duchesnehouston)", "url": "https://www.instagram.com/duchesnehouston"},
    "instagram_athletics": {"name": "Instagram (@duchesneathletics)", "url": "https://www.instagram.com/duchesneathletics"},
    "instagram_dance": {"name": "Instagram (@chargergirlsdance)", "url": "https://www.instagram.com/chargergirlsdance/"},
    "instagram_arts": {"name": "Instagram (@duchesne_arts)", "url": "https://www.instagram.com/duchesne_arts/"},
    "instagram_upper": {"name": "Instagram (@duchesneupperschool)", "url": "https://www.instagram.com/duchesneupperschool"},
    "instagram_admissions": {"name": "Instagram (@duchesneadmissions)", "url": "https://www.instagram.com/duchesneadmissions/"},
    "instagram_alumnae": {"name": "Instagram (@duchesnealumnae)", "url": "https://www.instagram.com/duchesnealumnae"},
    "linkedin_main": {"name": "LinkedIn", "url": "https://www.linkedin.com/school/duchesne-academy-of-the-sacred-heart/"},
    "facebook_main": {"name": "Facebook", "url": "https://www.facebook.com/DuchesneAcademyHouston"},
    "facebook_athletics": {"name": "Facebook (Athletics & Campus Life)", "url": "https://www.facebook.com/profile.php?id=100079069373448"},
    "facebook_alumnae": {"name": "Facebook (Alumnae)", "url": "https://www.facebook.com/DuchesneHoustonAlums"},
    "youtube_main": {"name": "YouTube", "url": "https://www.youtube.com/@duchesneacademyofthesacred1409"}
}

@dataclass
class SocialPost:
    channel: str
    channel_name: str
    url: str
    caption: str
    timestamp: str

@dataclass
class UnifiedSocialStory:
    story_id: str
    headline: str
    summary: str
    timestamp: str
    source_links: Dict[str, str] = field(default_factory=dict)

def normalize_caption(caption: str) -> str:
    # Remove URLs
    text = re.sub(r'https?://\S+', '', caption)
    # Remove hashtags
    text = re.sub(r'#\w+', '', text)
    # Remove punctuation & emojis, normalize spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    return " ".join(text.lower().split())

def calculate_token_jaccard(text_a: str, text_b: str) -> float:
    tokens_a = set(normalize_caption(text_a).split())
    tokens_b = set(normalize_caption(text_b).split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0

def deduplicate_posts(posts: List[SocialPost], similarity_threshold: float = 0.70) -> List[UnifiedSocialStory]:
    stories = []
    merged_indices = set()

    for i, post in enumerate(posts):
        if i in merged_indices:
            continue

        headline = post.caption.split("\n")[0][:80].strip() or "Duchesne Social Update"
        summary = post.caption[:250].strip()
        source_links = {post.channel_name: post.url}
        merged_indices.add(i)

        for j in range(i + 1, len(posts)):
            if j in merged_indices:
                continue
            sim = calculate_token_jaccard(post.caption, posts[j].caption)
            if sim >= similarity_threshold:
                source_links[posts[j].channel_name] = posts[j].url
                merged_indices.add(j)

        stories.append(UnifiedSocialStory(
            story_id=f"story_{len(stories) + 1}",
            headline=headline,
            summary=summary,
            timestamp=post.timestamp[:10] if len(post.timestamp) >= 10 else post.timestamp,
            source_links=source_links
        ))
    return stories

def format_social_digest(stories: List[UnifiedSocialStory]) -> str:
    if not stories:
        return "### 📱 Duchesne Social Media Highlights\n*(No new social updates this period)*"

    lines = ["### 📱 Duchesne Social Media Highlights (Unified & Deduplicated)"]
    for story in stories:
        date_str = f" — *{story.timestamp}*" if story.timestamp else ""
        lines.append(f"\n* **{story.headline}**{date_str}")
        lines.append(f"  * *Summary:* {story.summary}")
        link_str = " · ".join([f"[{k}]({v})" for k, v in story.source_links.items()])
        lines.append(f"  * 🔗 **View on:** {link_str}")
    return "\n".join(lines)
