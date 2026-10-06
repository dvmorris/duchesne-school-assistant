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
