# payout

Helpers for sharing out money that is held as whole cents.

## `allocate(total, weights, caps=None) -> list[int]`

Splits `total` cents between parties in proportion to their `weights`. Money is never created or lost: the result
has one entry per weight, in the same order, and always adds up to exactly `total`. The lists you pass in are not
modified.

### Plain split

- A party's share is `total * weight / sum(weights)`, rounded down to whole cents.
- The cents left over after rounding down are handed out one each, to the parties with the largest fractional
  remainders. Parties whose remainders are equal are served in the order they appear in `weights`.
- A party with weight `0` never gets anything.

`allocate(100, [1, 1, 1])` is `[34, 33, 33]`, and `allocate(1000, [1, 2])` is `[333, 667]`.

### Caps

`caps` is an optional list with one maximum per party (whole cents, `0` or more). No party gets more than its cap.
Caps are applied in rounds:

1. Split the money that is still unassigned between the parties that are not fixed yet, using the plain rule.
2. Every party whose share is above its cap is fixed at its cap, all in the same round. The next round splits what
   remains between the other parties.
3. Stop when a round has no party above its cap.

`allocate(90, [1, 1, 1], caps=[10, 80, 80])` is `[10, 40, 40]`.

### Errors

`allocate` raises `ValueError` when

- `total` is negative;
- `weights` is empty, has a negative entry, or adds up to zero;
- `caps` is given with a different length than `weights`, or has a negative entry;
- the parties with a positive weight cannot hold `total` between them (their caps add up to less than `total`).
