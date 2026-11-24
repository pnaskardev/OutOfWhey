# Checks run a headless browser and read the shop's own API responses

The Amul Shop's pages are a JavaScript app: the raw HTML contains no Stock Status. Its JSON API (`/api/1/entity/ms.products`) needs a per-request `tid` signature (`<ms timestamp>:<n>:<sha256 hex>`) computed by the page's JavaScript, and Cloudflare bot cookies. So a Check loads the Product page in headless Chromium (Playwright), sets the Delivery Pincode the way a visitor does, and reads stock fields (`available`, `inventory_quantity`) from the `ms.products` responses the page itself receives. It does not match text on the page.

## Considered Options

- **Plain HTTP fetch + text match** (the original standard-library plan): impossible, because the HTML holds no stock data.
- **Calling the API directly** by copying the `tid` signing: fast and standard-library only, but it breaks whenever the shop redeploys its JavaScript, and it works around a deliberate anti-bot control. Rejected. Revisit only if browser Checks become too slow or get blocked.
- **Matching rendered button text** ("Sold Out" / "Add to Cart"): both strings appear on the page at once, so it is ambiguous. Rejected in favour of structured fields.

## Consequences

- Playwright + Chromium is the project's one dependency. Everything else is standard library only.
- Stock Status is scoped to a Substore (the `substore` query parameter), which the shop derives from the Delivery Pincode. Without a pincode it falls back to the requester's IP location, which is a US datacenter on GitHub Actions.
- Unverified until the first real run: whether Cloudflare lets headless Chromium from GitHub Actions through.
