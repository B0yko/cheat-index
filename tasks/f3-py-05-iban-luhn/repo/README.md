# bankcheck

Checks for account and card numbers that people type in by hand.

## `luhn_valid(number: str) -> bool`

Whether `number` passes the Luhn check used for payment cards and many other identification numbers.

- Spaces and hyphens may be used to group the digits and are ignored.
- Any other character makes the number invalid, and so does having fewer than two digits.
- Counting from the right, every second digit (the 2nd, 4th, ...) is doubled, and a doubled value above 9 has 9
  subtracted. The number is valid when the sum of all the digits is a multiple of 10.

`luhn_valid("7421 5036 8811 2")` is `True`; changing its last digit makes it `False`.

## `iban_valid(iban: str) -> bool`

Whether `iban` is a well-formed IBAN with correct check digits.

- Spaces are ignored and lowercase letters are accepted. What remains must consist of the letters A-Z and the
  digits 0-9 only.
- The first two characters are the country code (letters), the next two are the check digits (digits), the rest is
  the account part.
- The total length must be the one registered for the country. Only these countries are known, any other country
  code is invalid: AT 20, BE 16, CH 21, DE 22, DK 18, ES 24, FR 27, GB 22, IE 22, IT 27, LU 20, NL 18, NO 15,
  PL 28, PT 25, SE 24.
- Check: move the first four characters to the end, replace every letter by its number (`A` is 10, `B` is 11, up
  to `Z` is 35) and read the result as one large integer. The IBAN is valid when that integer leaves remainder 1
  when divided by 97.

`iban_valid("BE14 7310 4520 9876")` is `True`.

## `iban_check_digits(country: str, account: str) -> str`

Returns the two check digits to place after `country` in the IBAN for this account part. Build the number from
`account`, then `country`, then `00` (letters converted as above); the check digits are 98 minus the remainder of
that number divided by 97, written with two digits (`"07"`, not `"7"`).

`country` must be two letters and `account` must be non-empty and consist of letters and digits only (no spaces),
both in either case; anything else raises `ValueError`. The country does not have to be one of the known
countries.

`iban_check_digits("BE", "731045209876")` is `"14"`, which gives `BE14731045209876`.
