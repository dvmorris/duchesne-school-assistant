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
        self.assertEqual(items[0].product_url, "https://duchesnespiritstore.square.site/product/fleece/1")

    def test_parse_store_catalog_from_bootstrap_string(self):
        sample_html = """
        <html>
        <head>
        <script>
        window.__DYNAMIC_BOOTSTRAP__ = {"products": [{"id": 42, "title": "Charger Hoodie", "price": "$55.00", "category": "Outerwear", "url": "https://duchesnespiritstore.square.site/product/42"}]};
        </script>
        </head>
        </html>
        """
        items = parse_store_catalog(sample_html)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "42")
        self.assertEqual(items[0].title, "Charger Hoodie")
        self.assertEqual(items[0].price, "$55.00")

    def test_detect_new_and_featured(self):
        item1 = StoreItem(id="item_1", title="Navy Fleece Full-Zip", price="$48.00", category="Outerwear", product_url="https://duchesnespiritstore.square.site/product/1")
        item2 = StoreItem(id="item_2", title="Charger Spirit T-Shirt", price="$20.00", category="Apparel", product_url="https://duchesnespiritstore.square.site/product/2")
        items = [item1, item2]

        known_ids = ["item_2"]
        new_items, featured = detect_new_and_featured(items, known_ids, season="fall")
        self.assertEqual(len(new_items), 1)
        self.assertEqual(new_items[0].id, "item_1")
        self.assertTrue(new_items[0].is_new_arrival)
        self.assertTrue(any("Fleece" in f.title for f in featured))

    def test_detect_new_and_featured_spring(self):
        item1 = StoreItem(id="item_1", title="Charger Spirit T-Shirt", price="$20.00", category="Apparel", product_url="https://...")
        item2 = StoreItem(id="item_2", title="Winter Parka", price="$120.00", category="Outerwear", product_url="https://...")
        items = [item1, item2]

        new_items, featured = detect_new_and_featured(items, known_ids=[], season="spring")
        self.assertEqual(len(new_items), 2)
        self.assertTrue(any("T-Shirt" in f.title for f in featured))

    def test_detect_new_and_featured_fallback(self):
        item1 = StoreItem(id="item_1", title="Notebook", price="$5.00", category="Supplies", product_url="https://...")
        items = [item1]

        new_items, featured = detect_new_and_featured(items, known_ids=[], season="fall")
        self.assertEqual(len(featured), 1)
        self.assertEqual(featured[0].id, "item_1")

    def test_format_store_digest(self):
        new_item = StoreItem(id="item_1", title="Navy Fleece", price="$48.00", category="Outerwear", product_url="https://duchesnespiritstore.square.site/product/1", is_new_arrival=True)
        featured = [StoreItem(id="item_2", title="Spirit Shirt", price="$20.00", category="Apparel", product_url="https://duchesnespiritstore.square.site/product/2")]
        output = format_store_digest([new_item], featured)
        self.assertIn("Navy Fleece", output)
        self.assertIn("Spirit Shirt", output)
        self.assertIn("New Arrivals", output)
        self.assertIn("Seasonal Featured Picks", output)

    def test_format_store_digest_empty_new_arrivals(self):
        featured = [StoreItem(id="item_2", title="Spirit Shirt", price="$20.00", category="Apparel", product_url="https://duchesnespiritstore.square.site/product/2")]
        output = format_store_digest([], featured)
        self.assertIn("(No new arrivals this week)", output)
        self.assertIn("Spirit Shirt", output)

if __name__ == "__main__":
    unittest.main()
