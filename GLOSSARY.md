# OutOfWhey

A personal stock watcher. It alerts the user when a Product they want comes back in stock on the Amul Shop, so they can order it themselves.

## Language

**Amul Shop**:
Amul's official online store (shop.amul.com), the only source of Stock Status.
_Avoid_: Amul website, store, Blinkit/Zepto (out of scope)

**Product**:
One item sold on the Amul Shop, such as a specific pack size of whey protein.
_Avoid_: item, SKU, listing

**Watchlist**:
The Products the user wants alerts for.
_Avoid_: tracked products, subscriptions

**Delivery Pincode**:
The single pincode that Stock Status is read against.
_Avoid_: location, zip

**Substore**:
The Amul Shop's fulfilment area that a Delivery Pincode belongs to. Stock Status is held per Substore.
_Avoid_: warehouse, region, store

**Stock Status**:
Whether a Product is In Stock or Sold Out on the Amul Shop for the Delivery Pincode's Substore.
_Avoid_: availability, inventory

**Check**:
One reading of a Product's Stock Status.
_Avoid_: poll, scrape

**Failed Check**:
A Check that could not read a Product's Stock Status. It leaves the last known Stock Status unchanged.
_Avoid_: error, unknown status

**Restock**:
A Product going from Sold Out to In Stock between two consecutive Checks.
_Avoid_: back-in-stock event, availability change

**Alert**:
The message the user receives when a Restock happens. Ordering stays manual: an Alert never places an order.
_Avoid_: notification, ping
