# bytesize

Parse and format human-readable file sizes such as `1.5 kB` or `300 MiB`.

## Units

| Unit | Bytes |
| --- | --- |
| `B` | 1 |
| `kB`, `MB`, `GB`, `TB` | 1000, 1000^2, 1000^3, 1000^4 (decimal) |
| `KiB`, `MiB`, `GiB`, `TiB` | 1024, 1024^2, 1024^3, 1024^4 (binary) |

Unit names are not case sensitive: `kb` is `kB` and `gib` is `GiB`.

## `parseSize(text: string): number`

Turns a size into a number of bytes. The text is digits with an optional decimal part, optional whitespace and an
optional unit; without a unit the number is bytes. Leading and trailing whitespace is ignored. The result is rounded to
the nearest whole byte.

- `parseSize("512")` is `512`
- `parseSize("1.5 kB")` is `1500`
- `parseSize("1.5 KiB")` is `1536`
- `parseSize("3 MB")` is `3000000`

Anything else (an empty string, a sign, a missing number, an unknown unit such as `5 XB`) throws a `RangeError` whose
message starts with `invalid size`.

## `formatSize(bytes: number, options?: { binary?: boolean; digits?: number }): string`

Formats a byte count. `bytes` must be a non-negative safe integer, otherwise `RangeError`.

- `binary` (default `false`) selects the 1024-based units, otherwise the decimal ones are used.
- `digits` (default `1`, from 0 to 6) is the number of decimals; trailing zeros are removed.
- A count below one unit is shown in bytes: `999` is `"999 B"`.
- Otherwise the largest unit that keeps the value at 1 or more is used: `1500` is `"1.5 kB"` and `2000000` is `"2 MB"`.
- If rounding makes the value reach the next unit, that unit is used instead: `999960` is `"1 MB"`, not `"1000 kB"`.
- There is nothing above `TB`/`TiB`; larger values stay in that unit (`"5000 TB"`).
