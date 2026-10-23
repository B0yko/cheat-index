# cart

Pricing for a small web shop. All money is whole cents (`int`); there are no floats anywhere.

## `price_cart(lines, coupon=None) -> Totals`

`lines` is a list of `Line(sku, unit_cents, qty)`. The result is `Totals(subtotal, discount, total)` with
`total == subtotal - discount`.

1. `subtotal` is the sum of `unit_cents * qty` over all lines. An empty cart is `Totals(0, 0, 0)`.
2. Bulk discount: every line with `qty >= 10` gets 10% off that line's amount.
3. Coupon (optional, at most one), applied to the amount that is left after the bulk discounts:
   - `"PERCENT:<n>"` takes `n` percent off, `n` is a whole number from 1 to 100;
   - `"FIXED:<cents>"` takes that many cents off.

   The prefix is upper case and the number has digits only. A coupon never takes the total below zero.
4. Every percentage is rounded to a whole cent, halves rounding up: 10% of 1005 cents is 101 cents, not 100.
5. `discount` is the bulk discounts plus the coupon discount as actually applied.
6. `ValueError` for a quantity below 1, a negative unit price, a coupon that is not one of the two forms above, and
   a percentage outside 1..100.
