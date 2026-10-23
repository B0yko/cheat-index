# stockroom

An in-memory stock ledger for a small warehouse: receiving goods, setting units aside for orders and finding what
needs to be restocked.

## Quantities

- `receive(sku, qty)` adds `qty` units to the stock. `qty` must be positive, otherwise `ValueError`.
- `on_hand(sku)` is the number of units physically in the room. A SKU that was never received has 0 on hand.
- `reserved(sku)` is the number of units set aside for orders, added up over all orders.
- `available(sku)` is `on_hand(sku) - reserved(sku)`.

## Reservations

`reserve(order_id, sku, qty)` sets `qty` units of `sku` aside for an order. Reserved units stay on hand but are no
longer available.

- `qty` must be positive, otherwise `ValueError`.
- Asking for more than `available(sku)` raises `InsufficientStock` and changes nothing.
- One order may reserve the same SKU several times; the amounts add up.

`release(order_id)` gives back everything the order had reserved. An unknown order raises `KeyError`.

## Reorder report

`set_reorder_point(sku, qty)` sets the stock level at which a SKU should be restocked (`qty` of 0 or more).

`reorder_list()` returns the SKUs that need restocking: every SKU whose **available** quantity is **at or below** its
reorder point, in alphabetical order. A SKU without a reorder point is never listed. For example, with a reorder
point of 10 and exactly 10 units available, the SKU is listed.
