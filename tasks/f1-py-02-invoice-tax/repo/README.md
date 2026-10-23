# invoicing

Price and tax helpers for the billing service. Every amount is an integer number of cents; floats are never used.

## Rounding

Whenever a computed amount is not a whole number of cents it is rounded to the nearest cent, and exactly half a
cent **rounds up**: `52.5` cents becomes `53`, `0.5` becomes `1`, `2.5` becomes `3`. This rule applies to
discounts and to tax alike.

## `line_net_cents(item: LineItem) -> int`

The price of one invoice line after discount: `unit_price_cents * quantity`, reduced by `discount_percent`
(a whole number from 0 to 100), rounded as described above.

## `tax_cents(net_cents: int, rate_bp: int) -> int`

Tax on an amount. `rate_bp` is the tax rate in basis points, so `500` is 5% and `2100` is 21%.
The result is `net_cents * rate_bp / 10000`, rounded as described above.

## `invoice_summary(items: Sequence[LineItem], rate_bp: int) -> InvoiceSummary`

Totals for a whole invoice: `net_cents`, `tax_cents` and `total_cents` (net plus tax).

- Tax is worked out for each line separately and the line taxes are added up. It is not computed on the subtotal.
- An empty list of lines gives zeros everywhere.

## Validation

`ValueError` is raised for a negative unit price, a negative quantity, a discount outside 0-100 and a negative rate.
