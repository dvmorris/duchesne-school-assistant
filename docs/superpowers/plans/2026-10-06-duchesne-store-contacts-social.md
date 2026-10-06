# Duchesne School Assistant: Store, Contacts & Social Media Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Spirit Store inventory crawler, the Veracross directory contact exporter (vCard & CSV), and the 12-channel social media aggregator with cross-platform deduplication.

**Architecture:** Three modular Python engines (`spirit_store_crawler.py`, `directory_exporter.py`, `social_aggregator.py`) integrated into `dashboard_aggregator.py` and `veracross_scanner.py`. State is cached in `duchesne_state.json`. Zero external pip dependencies (Python standard library only).

**Tech Stack:** Python 3 (standard libraries: `json`, `re`, `urllib.request`, `urllib.parse`, `datetime`, `dataclasses`, `csv`, `unittest`).

**Spec:** [2026-10-06-duchesne-store-contacts-social-design.md](file://./docs/superpowers/specs/2026-10-06-duchesne-store-contacts-social-design.md)

## Global Constraints
- Python 3 standard library only (`json`, `re`, `urllib`, `dataclasses`, `csv`, `datetime`, `typing`).
- All vCard files must conform to vCard 3.0 / RFC 6350 specifications with proper escaping (`\n`, `\,`, `\;`).
- Google Contacts CSV must adhere to official Google Contacts header schemas.
- Social media caption deduplication uses token-level Jaccard similarity with a 0.70 threshold.
- All unit tests must use mocked responses or local fixtures without making unverified network requests.

---

### Task 1: Duchesne Spirit Store Crawler & Inventory Alerts

**Files:**
- Create: `./scripts/spirit_store_crawler.py`
- Test: `./tests/test_spirit_store_crawler.py`

**Interfaces:**
- Consumes: Catalog HTML / JSON bootstrap payloads.
- Produces:
  - `class StoreItem(id, title, price, category, product_url, image_url, is_new_arrival)`
  - `parse_store_catalog(catalog_data: str | dict) -> list[StoreItem]`
  - `detect_new_and_featured(items: list[StoreItem], known_ids: list[str], season: str = "fall") -> tuple[list[StoreItem], list[StoreItem]]`
  - `format_store_digest(new_arrivals: list[StoreItem], featured_items: list[StoreItem]) -> str`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from scripts.spirit_store_crawler import (
    StoreItem,
    parse_store_catalog,
    detect_new_and_featured,
    format_store_digest
)

class TestSpiritStoreCrawler(unittest.TestCase):
    def test_parse_store_catalog_from_json(self):
        sample_json = {
            "items": [
                {"id": "item_1", "name": "Navy Fleece Full-Zip", "price": "$48.00", "category": "Outerwear", "url": "/product/fleece/1"},
                {"id": "item_2", "name": "Plaid Hair Bow", "price": "$12.00", "category": "Accessories", "url": "/product/bow/2"}
            ]
        }
        items = parse_store_catalog(sample_json)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].id, "item_1")
        self.assertEqual(items[0].title, "Navy Fleece Full-Zip")
        self.assertEqual(items[0].price, "$48.00")

    def test_detect_new_and_featured(self):
        item1 = StoreItem(id="item_1", title="Navy Fleece Full-Zip", price="$48.00", category="Outerwear", product_url="https://...")
        item2 = StoreItem(id="item_2", title="Charger Spirit T-Shirt", price="$20.00", category="Apparel", product_url="https://...")
        items = [item1, item2]

        known_ids = ["item_2"]
        new_items, featured = detect_new_and_featured(items, known_ids, season="fall")
        self.assertEqual(len(new_items), 1)
        self.assertEqual(new_items[0].id, "item_1")
        self.assertTrue(new_items[0].is_new_arrival)
        self.assertTrue(any("Fleece" in f.title for f in featured))

    def test_format_store_digest(self):
        new_item = StoreItem(id="item_1", title="Navy Fleece", price="$48.00", category="Outerwear", product_url="https://duchesnespiritstore.square.site/product/1", is_new_arrival=True)
        featured = [StoreItem(id="item_2", title="Spirit Shirt", price="$20.00", category="Apparel", product_url="https://duchesnespiritstore.square.site/product/2")]
        output = format_store_digest([new_item], featured)
        self.assertIn("Navy Fleece", output)
        self.assertIn("Spirit Shirt", output)
        self.assertIn("New Arrivals", output)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest tests/test_spirit_store_crawler.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.spirit_store_crawler'`

- [ ] **Step 3: Write minimal implementation in `scripts/spirit_store_crawler.py`**

```python
import json
import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Union, Any

STORE_BASE_URL = "https://duchesnespiritstore.square.site"

FALL_KEYWORDS = ["fleece", "jacket", "sweatshirt", "hoodie", "outerwear", "cardigan", "sweater", "vest"]
SPRING_KEYWORDS = ["t-shirt", "spirit shirt", "cap", "hat", "polo", "shorts", "visor"]

@dataclass
class StoreItem:
    id: str
    title: str
    price: str
    category: str
    product_url: str
    image_url: str = ""
    is_new_arrival: bool = False

def parse_store_catalog(catalog_data: Union[str, Dict[str, Any]]) -> List[StoreItem]:
    items = []
    data = catalog_data
    if isinstance(catalog_data, str):
        # Look for bootstrap JSON or parse JSON directly
        bootstrap_match = re.search(r'window\.__DYNAMIC_BOOTSTRAP__\s*=\s*(\{.*?\});', catalog_data, re.DOTALL)
        if bootstrap_match:
            try:
                data = json.loads(bootstrap_match.group(1))
            except Exception:
                data = {}
        else:
            try:
                data = json.loads(catalog_data)
            except Exception:
                data = {}

    if isinstance(data, dict):
        raw_items = data.get("items", []) or data.get("products", [])
        for raw in raw_items:
            item_id = str(raw.get("id", ""))
            name = raw.get("name", "") or raw.get("title", "")
            price = str(raw.get("price", ""))
            category = raw.get("category", "") or "General Merchandise"
            url = raw.get("url", "") or f"/product/{item_id}"
            if not url.startswith("http"):
                url = STORE_BASE_URL + url
            items.append(StoreItem(
                id=item_id,
                title=name,
                price=price,
                category=category,
                product_url=url,
                image_url=raw.get("image_url", "")
            ))
    return items

def detect_new_and_featured(
    items: List[StoreItem],
    known_ids: List[str],
    season: str = "fall"
) -> Tuple[List[StoreItem], List[StoreItem]]:
    new_arrivals = []
    known_set = set(known_ids)
    keywords = FALL_KEYWORDS if season.lower() in ["fall", "winter"] else SPRING_KEYWORDS

    for item in items:
        if item.id not in known_set:
            item.is_new_arrival = True
            new_arrivals.append(item)

    # Pick 2-3 featured seasonal items
    featured = []
    for item in items:
        if any(k in item.title.lower() or k in item.category.lower() for k in keywords):
            featured.append(item)
            if len(featured) >= 3:
                break

    # Fallback featured if no keyword matches
    if not featured and items:
        featured = items[:3]

    return new_arrivals, featured

def format_store_digest(new_arrivals: List[StoreItem], featured_items: List[StoreItem]) -> str:
    lines = ["### 🛍️ Duchesne Spirit Store: New Arrivals & Featured Picks"]

    if new_arrivals:
        lines.append("* **🆕 New Arrivals:**")
        for item in new_arrivals:
            lines.append(f"  - [{item.title} ({item.price})]({item.product_url}) — *Category: {item.category}*")
    else:
        lines.append("*(No new arrivals this week)*")

    if featured_items:
        lines.append("* **⭐ Seasonal Featured Picks:**")
        for item in featured_items:
            lines.append(f"  - [{item.title} ({item.price})]({item.product_url})")

    lines.append(f"* 🔗 [Browse Full Spirit Store Online]({STORE_BASE_URL})")
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_spirit_store_crawler.py`
Expected: `Ran 3 tests in 0.00Xs ... OK`

- [ ] **Step 5: Commit**

```bash
git add scripts/spirit_store_crawler.py tests/test_spirit_store_crawler.py
git commit -m "feat(store): implement Spirit Store crawler and inventory alert engine"
```

---

### Task 2: Veracross Directory Crawler & Contact Exporter (vCard & CSV)

**Files:**
- Create: `./scripts/directory_exporter.py`
- Test: `./tests/test_directory_exporter.py`

**Interfaces:**
- Consumes: Directory roster data (list of parent/student dicts or HTML).
- Produces:
  - `class ParentContact(first_name, last_name, email, phone, child_name, child_grade, address)`
  - `parse_directory_roster(roster_data: list[dict] | str) -> list[ParentContact]`
  - `generate_vcard_content(contacts: list[ParentContact]) -> str`
  - `generate_google_contacts_csv(contacts: list[ParentContact]) -> str`
  - `export_contacts(contacts: list[ParentContact], vcf_path: str, csv_path: str) -> None`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from scripts.directory_exporter import (
    ParentContact,
    generate_vcard_content,
    generate_google_contacts_csv
)

class TestDirectoryExporter(unittest.TestCase):
    def test_generate_vcard_content(self):
        contact = ParentContact(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="(713) 555-0123",
            child_name="Clara Davis",
            child_grade="PK4",
            address="10202 Memorial Dr, Houston, TX 77024"
        )
        vcard = generate_vcard_content([contact])
        self.assertIn("BEGIN:VCARD", vcard)
        self.assertIn("VERSION:3.0", vcard)
        self.assertIn("FN:Jane Doe", vcard)
        self.assertIn("EMAIL;TYPE=INTERNET,HOME:jane.doe@example.com", vcard)
        self.assertIn("TITLE:Parent of Clara Davis (PK4)", vcard)
        self.assertIn("END:VCARD", vcard)

    def test_generate_google_contacts_csv(self):
        contact = ParentContact(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="(713) 555-0123",
            child_name="Clara Davis",
            child_grade="PK4"
        )
        csv_content = generate_google_contacts_csv([contact])
        self.assertIn("Given Name,Family Name", csv_content)
        self.assertIn("Jane,Doe", csv_content)
        self.assertIn("jane.doe@example.com", csv_content)
        self.assertIn("Parent of Clara Davis (PK4)", csv_content)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest tests/test_directory_exporter.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.directory_exporter'`

- [ ] **Step 3: Write minimal implementation in `scripts/directory_exporter.py`**

```python
import csv
import io
import re
from dataclasses import dataclass
from typing import List, Dict, Union, Any

@dataclass
class ParentContact:
    first_name: str
    last_name: str
    email: str
    phone: str
    child_name: str
    child_grade: str
    address: str = ""

def parse_directory_roster(roster_data: Union[List[Dict[str, Any]], str]) -> List[ParentContact]:
    contacts = []
    if isinstance(roster_data, list):
        for entry in roster_data:
            contacts.append(ParentContact(
                first_name=entry.get("first_name", "").strip(),
                last_name=entry.get("last_name", "").strip(),
                email=entry.get("email", "").strip(),
                phone=entry.get("phone", "").strip(),
                child_name=entry.get("child_name", "").strip(),
                child_grade=entry.get("child_grade", "").strip(),
                address=entry.get("address", "").strip()
            ))
    elif isinstance(roster_data, str):
        # Fallback HTML parser looking for parent cards
        parent_cards = re.findall(r'<div class="parent-entry"[^>]*>(.*?)</div>', roster_data, re.DOTALL)
        for card in parent_cards:
            fn = re.search(r'class="first-name">([^<]+)', card)
            ln = re.search(r'class="last-name">([^<]+)', card)
            em = re.search(r'mailto:([^\"]+)', card)
            ph = re.search(r'tel:([^\"]+)', card)
            ch = re.search(r'class="student-name">([^<]+)', card)
            gr = re.search(r'class="grade">([^<]+)', card)
            if fn and ln:
                contacts.append(ParentContact(
                    first_name=fn.group(1).strip(),
                    last_name=ln.group(1).strip(),
                    email=em.group(1).strip() if em else "",
                    phone=ph.group(1).strip() if ph else "",
                    child_name=ch.group(1).strip() if ch else "",
                    child_grade=gr.group(1).strip() if gr else ""
                ))
    return contacts

def generate_vcard_content(contacts: List[ParentContact]) -> str:
    cards = []
    for c in contacts:
        card = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{c.first_name} {c.last_name}".strip(),
            f"N:{c.last_name};{c.first_name};;;",
            f"EMAIL;TYPE=INTERNET,HOME:{c.email}" if c.email else "",
            f"TEL;TYPE=CELL:{c.phone}" if c.phone else "",
            "ORG:Duchesne Academy of the Sacred Heart",
            f"TITLE:Parent of {c.child_name} ({c.child_grade})" if c.child_name else "TITLE:Duchesne Parent",
            f"NOTE:Student: {c.child_name} | Grade: {c.child_grade} | Duchesne Academy Parent Directory",
            f"ADR;TYPE=HOME:;;{c.address};;;;" if c.address else "",
            "END:VCARD"
        ]
        cards.append("\n".join([line for line in card if line]))
    return "\n\n".join(cards) + "\n"

def generate_google_contacts_csv(contacts: List[ParentContact]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Given Name", "Family Name",
        "E-mail 1 - Type", "E-mail 1 - Value",
        "Phone 1 - Type", "Phone 1 - Value",
        "Organization 1 - Name", "Organization 1 - Title",
        "Notes", "Address 1 - Formatted"
    ])

    for c in contacts:
        writer.writerow([
            f"{c.first_name} {c.last_name}".strip(),
            c.first_name,
            c.last_name,
            "Home", c.email,
            "Mobile", c.phone,
            "Duchesne Academy of the Sacred Heart",
            f"Parent of {c.child_name} ({c.child_grade})" if c.child_name else "Duchesne Parent",
            f"Student: {c.child_name} | Grade: {c.child_grade}",
            c.address
        ])
    return output.getvalue()

def export_contacts(contacts: List[ParentContact], vcf_path: str, csv_path: str) -> None:
    vcf_content = generate_vcard_content(contacts)
    with open(vcf_path, "w", encoding="utf-8") as f:
        f.write(vcf_content)

    csv_content = generate_google_contacts_csv(contacts)
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_directory_exporter.py`
Expected: `Ran 2 tests in 0.00Xs ... OK`

- [ ] **Step 5: Commit**

```bash
git add scripts/directory_exporter.py tests/test_directory_exporter.py
git commit -m "feat(directory): implement directory crawler and vCard/CSV contact exporter"
```

---

### Task 3: 12-Channel Social Media Aggregator & Deduplication Engine

**Files:**
- Create: `./scripts/social_aggregator.py`
- Test: `./tests/test_social_aggregator.py`

**Interfaces:**
- Consumes: Post data across the 12 Duchesne social channels.
- Produces:
  - `class SocialPost(channel, channel_name, url, caption, timestamp)`
  - `class UnifiedSocialStory(story_id, headline, summary, timestamp, source_links)`
  - `normalize_caption(caption: str) -> str`
  - `calculate_token_jaccard(text_a: str, text_b: str) -> float`
  - `deduplicate_posts(posts: list[SocialPost], similarity_threshold: float = 0.70) -> list[UnifiedSocialStory]`
  - `format_social_digest(stories: list[UnifiedSocialStory]) -> str`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from scripts.social_aggregator import (
    SocialPost,
    UnifiedSocialStory,
    normalize_caption,
    calculate_token_jaccard,
    deduplicate_posts,
    format_social_digest
)

class TestSocialAggregator(unittest.TestCase):
    def test_normalize_caption(self):
        raw = "Varsity Volleyball sweeps Episcopal! 🏐 #chargers #duchesnehouston https://bit.ly/123"
        normalized = normalize_caption(raw)
        self.assertNotIn("https://", normalized)
        self.assertNotIn("#chargers", normalized)
        self.assertIn("varsity volleyball sweeps episcopal", normalized)

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

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest tests/test_social_aggregator.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.social_aggregator'`

- [ ] **Step 3: Write minimal implementation in `scripts/social_aggregator.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest -v tests/test_social_aggregator.py`
Expected: `Ran 3 tests in 0.00Xs ... OK`

- [ ] **Step 5: Commit**

```bash
git add scripts/social_aggregator.py tests/test_social_aggregator.py
git commit -m "feat(social): implement 12-channel social media aggregator and deduplicator"
```

---

### Task 4: CLI Scanner Integration & Report Extension

**Files:**
- Modify: `./scripts/dashboard_aggregator.py`
- Modify: `./scripts/veracross_scanner.py`
- Test: `./tests/test_veracross_scanner.py`

**Interfaces:**
- Extend `synthesize_family_digest` with optional `store_section: str` and `social_section: str`.
- Extend `veracross_scanner.py` with actions: `store`, `contacts`, `social`.

- [ ] **Step 1: Write the failing test**

In `tests/test_veracross_scanner.py`, add:
```python
    def test_cli_store_and_social_actions(self):
        # Test store action
        res_store = subprocess.run(
            [sys.executable, "./scripts/veracross_scanner.py", "--action", "store"],
            capture_output=True, text=True
        )
        self.assertEqual(res_store.returncode, 0)
        self.assertIn("Spirit Store", res_store.stdout)

        # Test social action
        res_social = subprocess.run(
            [sys.executable, "./scripts/veracross_scanner.py", "--action", "social"],
            capture_output=True, text=True
        )
        self.assertEqual(res_social.returncode, 0)
        self.assertIn("Social Media Highlights", res_social.stdout)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest tests/test_veracross_scanner.py`
Expected: FAIL with unrecognized action `store`.

- [ ] **Step 3: Update `scripts/dashboard_aggregator.py` and `scripts/veracross_scanner.py`**
  - Add `store_section: Optional[str] = None` and `social_section: Optional[str] = None` to `synthesize_family_digest`.
  - Add actions `store`, `contacts`, and `social` to `scripts/veracross_scanner.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest discover -v -s tests`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/dashboard_aggregator.py scripts/veracross_scanner.py tests/test_veracross_scanner.py
git commit -m "feat(integration): integrate store, contacts, and social actions into veracross_scanner"
```

---

### Task 5: Documentation Update in `SKILL.md`

**Files:**
- Modify: `./SKILL.md`

- [ ] **Step 1: Update `SKILL.md`**
  - Document the Spirit Store crawler, new arrival alerts, and featured picks.
  - Document the Parent Directory crawler and how parents can download/use `.vcf` and `.csv` contact exports.
  - Document the 12-channel social media aggregator and deduplication behavior.
  - Document the updated CLI actions (`--action store`, `--action contacts`, `--action social`).

- [ ] **Step 2: Verify all tests**
  - Run `PYTHONPATH=. python3 -m unittest discover tests`.
  - Commit documentation updates.
