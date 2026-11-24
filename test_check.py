import unittest

from check import CheckFailed, Stock, is_product_response, slug_from_url, stock_from_body

SLUG = "amul-whey-protein-32-g-or-pack-of-30-sachets"
API = "https://shop.amul.com/api/1/entity/ms.products"


class SlugFromUrl(unittest.TestCase):
    def test_product_page(self):
        url = f"https://shop.amul.com/en/product/{SLUG}"
        self.assertEqual(slug_from_url(url), SLUG)

    def test_trailing_slash_and_query(self):
        url = f"https://shop.amul.com/en/product/{SLUG}/?utm=x"
        self.assertEqual(slug_from_url(url), SLUG)

    def test_rejects_other_hosts_and_pages(self):
        for url in [f"https://example.com/en/product/{SLUG}",
                    "https://shop.amul.com/en/browse/protein", ""]:
            with self.assertRaises(ValueError):
                slug_from_url(url)


class IsProductResponse(unittest.TestCase):
    def test_matches_own_alias_query(self):
        url = f'{API}?q=%7B%22alias%22:%22{SLUG}%22%7D&limit=1'
        self.assertTrue(is_product_response(url, SLUG))

    def test_ignores_other_products_and_listings(self):
        other = f'{API}?q=%7B%22alias%22:%22something-else%22%7D'
        listing = f"{API}?filters%5B0%5D%5Bfield%5D=categories&substore=abc"
        bad_json = f"{API}?q=not-json"
        redirects = f'https://shop.amul.com/api/1/entity/ms.redirects?q=%7B%22alias%22:%22{SLUG}%22%7D'
        for url in [other, listing, bad_json, redirects]:
            self.assertFalse(is_product_response(url, SLUG), url)


class StockFromBody(unittest.TestCase):
    def test_available_decides_not_quantity(self):
        body = {"data": [{"name": "Whey", "available": 0, "inventory_quantity": 5}]}
        self.assertEqual(stock_from_body(body), Stock("Whey", False))

    def test_in_stock(self):
        self.assertEqual(stock_from_body({"data": [{"name": "Whey", "available": 1}]}),
                         Stock("Whey", True))

    def test_failed_checks(self):
        for body in [{"data": []}, {}, {"data": [{"name": "Whey"}]}]:
            with self.assertRaises(CheckFailed):
                stock_from_body(body)


if __name__ == "__main__":
    unittest.main()
