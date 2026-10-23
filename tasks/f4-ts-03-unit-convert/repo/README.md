# unit-kit

Conversions between common units for a recipe and shipping tool. Unit symbols are case-sensitive.

| Kind        | Symbols                          |
| ----------- | -------------------------------- |
| length      | `mm` `cm` `m` `km` `in` `ft` `yd` `mi` |
| mass        | `mg` `g` `kg` `oz` `lb`          |
| temperature | `C` `F` `K`                      |

The factors for lengths and masses are in `src/units.ts`.

## `convert(value, from, to): number`

Converts a number between two units of the same kind. The result is not rounded; converting to the same unit returns
the value unchanged.

- Temperatures: Celsius to Fahrenheit is `c * 9 / 5 + 32`, Kelvin is Celsius plus 273.15.
- A temperature below absolute zero (below `-273.15 C`, `-459.67 F` or `0 K`, checked in the unit it is given in)
  throws a `RangeError`.
- An unknown symbol throws `Error("unknown unit: <symbol>")`; if both are unknown the `from` symbol is reported.
- Units of different kinds throw `Error("cannot convert <from> to <to>")`, for example `cannot convert kg to m`.

## `parseQuantity(text): { value, unit }`

Reads a number, optional spaces and a unit symbol, for example `"12.5 kg"`, `"-3C"` or `"  1e3 m "`. The number can have
a sign, a decimal part and an exponent (`.5`, `5.`, `1.5e-3` are fine). Whether the symbol is a known unit is not
checked here. Anything else throws `Error("cannot parse quantity: <text>")` with the text as it was given.

## `convertText(text, to, digits = 2): string`

Parses `text`, converts it to the unit `to` and formats the result as `"<number> <to>"`. The number is rounded to `digits`
decimals and printed without trailing zeros, and a rounded zero is always printed as `0`:

```ts
convertText("5 km", "mi");   // "3.11 mi"
convertText("1 m", "cm");    // "100 cm"
```
