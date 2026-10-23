# verkit

Helpers for semantic version strings such as `1.4.2` or `2.0.0-rc.1`.

## `parseVersion(text: string): Version`

Accepts `MAJOR.MINOR.PATCH`, optionally followed by a pre-release part after `-` (identifiers made of `0-9A-Za-z-`
separated by dots) and build metadata after `+`. A leading `v` and surrounding whitespace are allowed. The result is
`{ major, minor, patch, prerelease }` where `prerelease` is the list of identifiers (empty for a plain release); build
metadata is dropped. Anything else throws an `Error` whose message starts with `invalid version`.

## `compareVersions(a: string, b: string): -1 | 0 | 1`

Returns `-1` when `a` has lower precedence than `b`, `1` when it has higher precedence and `0` when they are equal.

1. `major`, `minor` and `patch` are compared as numbers (`1.10.0` is greater than `1.9.0`).
2. When those are equal, a version **with** a pre-release has *lower* precedence than the same version without one:
   `1.0.0-rc.1` comes before `1.0.0`.
3. Two pre-releases are compared identifier by identifier, left to right. Numeric identifiers are compared as numbers,
   other identifiers in plain ASCII order, and a numeric identifier is lower than a non-numeric one. If all shared
   identifiers are equal, the pre-release with fewer identifiers is lower (`1.0.0-alpha` before `1.0.0-alpha.1`).
4. Build metadata is ignored.

## `sortVersions(versions: string[]): string[]`

A new array in ascending precedence order. Versions of equal precedence keep their original order.

## `latestStable(versions: string[]): string | undefined`

The highest version that has no pre-release part, or `undefined` when there is none.
