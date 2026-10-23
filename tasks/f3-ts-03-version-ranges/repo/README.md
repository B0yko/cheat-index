# verrange

Checks version numbers against dependency ranges such as `^1.2.3` or `>=1.2 <2`.

A **version** is three non-negative whole numbers separated by dots, like `1.12.0`. Numbers are compared as
numbers, so `1.10.0` is newer than `1.9.0`. Anything else (`1.2`, `v1.2.3`, `1.2.3-beta`, ...) is not a version, and
both functions throw an `Error` for it.

## `satisfies(version: string, range: string): boolean`

A **range** is one or more *sets* separated by `||`. A version satisfies the range when it satisfies at least one
set. A set is made of *comparators* separated by whitespace, and the version has to satisfy all of them. A set
without comparators, so also the empty range, is satisfied by every version.

### Partial versions

The minor and patch number may be left out, or written as `x`, `X` or `*`. Once a number is replaced by a wildcard,
the numbers after it have to be wildcards or left out too (`1.x.3` is an error).

### Comparators

A comparator is an optional operator directly followed by a (possibly partial) version, without a space:
`>=1.2.3`.

| comparator    | meaning                                                                            |
|---------------|------------------------------------------------------------------------------------|
| `1.2.3`, `=1.2.3` | exactly that version                                                           |
| `1.2`, `1.2.x`    | `>=1.2.0 <1.3.0`                                                               |
| `1`, `1.x`        | `>=1.0.0 <2.0.0`                                                               |
| `*`, `x`          | every version                                                                  |
| `>=1.2.3`     | that version or newer. `>=1.2` is `>=1.2.0`, and `>=1` is `>=1.0.0`                |
| `>1.2.3`      | newer than that version. `>1.2` is `>=1.3.0`, and `>1` is `>=2.0.0`               |
| `<1.2.3`      | older than that version. `<1.2` is `<1.2.0`, and `<1` is `<1.0.0`                 |
| `<=1.2.3`     | that version or older. `<=1.2` is `<1.3.0`, and `<=1` is `<2.0.0`                 |
| `~1.2.3`      | `>=1.2.3 <1.3.0`. `~1.2` is `>=1.2.0 <1.3.0`, and `~1` is `>=1.0.0 <2.0.0`        |
| `^1.2.3`      | changes that keep the left-most non-zero number: `>=1.2.3 <2.0.0`                 |

For `^`, a leading zero moves the limit: `^0.2.3` is `>=0.2.3 <0.3.0` and `^0.0.3` is `>=0.0.3 <0.0.4`. With a
partial version, `^1.2` is `>=1.2.0 <2.0.0`, `^0.2` is `>=0.2.0 <0.3.0`, `^0.0` is `>=0.0.0 <0.1.0`, `^0` is
`>=0.0.0 <1.0.0` and `^1` is `>=1.0.0 <2.0.0`.

Every operator needs at least a major number, so `>=x` and `^*` are errors.

### Hyphen ranges

`A - B`, with spaces around the hyphen, is a comparator pair that includes both ends: `1.2.3 - 2.3.4` is
`>=1.2.3 <=2.3.4`. A partial lower end is filled up with zeros and a partial upper end covers everything it names:
`1.2 - 2.3` is `>=1.2.0 <2.4.0`, and `1 - 2` is `>=1.0.0 <3.0.0`. Both ends need a major number and no operator.

### Errors

Anything that does not fit this syntax (`>=`, `1.2.3.4`, `>= 1.2.3`, `abc`, ...) makes `satisfies` throw an `Error`,
even when another set of the same range would have matched.

## `maxSatisfying(versions: string[], range: string): string | null`

The highest version in `versions` that satisfies `range`, returned as it is written in the list, or `null` when
none does. An invalid version in the list or an invalid range throws an `Error`.
