# pathrules

Selects file paths with an ordered list of glob patterns, like an allow/deny list.

## `new PathMatcher(patterns: string[])`

Paths are `/`-separated and relative, like `src/app/main.ts`. Each pattern is matched against the whole path, so
`*.ts` selects `main.ts` but not `src/main.ts`. The matcher keeps its own copy of the pattern list.

### Pattern syntax

- `*` matches any run of characters, also none, inside one path segment. It never matches `/`.
- `?` matches exactly one character other than `/`.
- A segment that is exactly `**` matches any number of whole segments, also none. `src/**/test.ts` matches
  `src/test.ts` and `src/a/b/test.ts`, and `**/x.ts` matches `x.ts` and `a/x.ts`. A trailing `/**` matches
  everything below the folder, so `src/**` matches `src/a` and `src/a/b.ts` but not `src` itself.
- `**` inside a longer segment (`a**b`) works like `*`.
- Every other character matches itself, case-sensitively. Characters such as `.`, `+`, `(`, `[` and `$` have no
  special meaning.

### Order and negation

A pattern that starts with `!` is a negation: the rest of it is the pattern, and a path that matches it is
deselected. The patterns are applied in order and the last one that matches a path decides. A path is selected if
that pattern is a normal one, and deselected if it is a `!` pattern. A path that matches no pattern is not selected.

## `matches(path: string): boolean`

Whether the path is selected.

## `filter(paths: string[]): string[]`

The selected paths, in their original order (a path that is listed twice is kept twice).

## `explain(path: string): string | null`

The pattern that decided about the path, exactly as it was given (with its `!` if it has one), or `null` when no
pattern matches the path.
