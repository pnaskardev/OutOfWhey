"""Check a Product's Stock Status on the Amul Shop for the Delivery Pincode.

See docs/adr/0001-browser-check-reads-shop-api-responses.md for why this drives a browser.

Usage: PINCODE=<pincode> python check.py <product page url>
"""

import json
import os
import sys
from typing import NamedTuple
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, Playwright, sync_playwright

SHOP_URL = "https://shop.amul.com/en/browse/protein"
TIMEOUT_MS = 30_000


class Stock(NamedTuple):
    name: str
    in_stock: bool


class CheckFailed(Exception):
    """The Check could not read the Product's Stock Status."""


def slug_from_url(product_url: str) -> str:
    parts = urlsplit(product_url)
    segments = [s for s in parts.path.split("/") if s]
    if parts.hostname != "shop.amul.com" or len(segments) < 2 or segments[-2] != "product":
        raise ValueError(f"Not an Amul Shop product page URL: {product_url!r}")
    return segments[-1]


def is_product_response(response_url: str, slug: str) -> bool:
    """True for the request the Product page makes to load its own Product."""
    parts = urlsplit(response_url)
    if not parts.path.endswith("/ms.products"):
        return False
    q = parse_qs(parts.query).get("q")
    if not q:
        return False
    try:
        return json.loads(q[0]).get("alias") == slug
    except (ValueError, AttributeError):
        return False


def stock_from_body(body: dict) -> Stock:
    data = body.get("data") or []
    if not data:
        raise CheckFailed("Product not found on the Amul Shop")
    product = data[0]
    if "available" not in product:
        raise CheckFailed("Stock Status field 'available' missing from the shop's response")
    # `available` is per Substore. `inventory_quantity` can be > 0 while `available` is 0.
    name = product.get("name") or product.get("alias", "?")
    return Stock(name=name, in_stock=bool(product["available"]))


def _is_set_preferences(response) -> bool:
    return urlsplit(response.url).path.endswith("/setPreferences")


def open_shop(playwright: Playwright, pincode: str) -> Page:
    """Open a browser session with the Delivery Pincode applied, as a visitor would."""
    page = playwright.chromium.launch().new_page()
    page.goto(SHOP_URL, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
    page.locator("#search").fill(pincode, timeout=TIMEOUT_MS)
    suggestion = page.locator(".searchitem-name").first
    try:
        suggestion.wait_for(timeout=TIMEOUT_MS)
    except PlaywrightError as e:
        raise CheckFailed("Delivery Pincode not recognised by the Amul Shop") from e
    with page.expect_response(_is_set_preferences, timeout=TIMEOUT_MS) as pref:
        suggestion.click()
    if not pref.value.ok:
        raise CheckFailed(f"Setting the Delivery Pincode failed: HTTP {pref.value.status}")
    return page


def check(page: Page, product_url: str) -> Stock:
    slug = slug_from_url(product_url)

    def is_ours(response) -> bool:
        return is_product_response(response.url, slug)

    nav = None
    try:
        with page.expect_response(is_ours, timeout=TIMEOUT_MS) as resp:
            nav = page.goto(product_url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
    except PlaywrightError as e:
        if nav is not None and nav.status >= 400:
            raise CheckFailed(f"Product page returned HTTP {nav.status}") from e
        first_line = e.message.splitlines()[0]
        raise CheckFailed(f"No Product data received from the shop: {first_line}") from e
    if nav is not None and nav.status >= 400:
        raise CheckFailed(f"Product page returned HTTP {nav.status}")
    if not resp.value.ok:
        raise CheckFailed(f"Shop API returned HTTP {resp.value.status}")
    return stock_from_body(resp.value.json())


def main() -> int:
    if len(sys.argv) != 2 or not os.environ.get("PINCODE"):
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    try:
        slug_from_url(sys.argv[1])
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    with sync_playwright() as p:
        try:
            stock = check(open_shop(p, os.environ["PINCODE"]), sys.argv[1])
        except CheckFailed as e:
            print(f"Failed Check: {e}")
            return 1
    print(f"{stock.name}: {'In Stock' if stock.in_stock else 'Sold Out'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
