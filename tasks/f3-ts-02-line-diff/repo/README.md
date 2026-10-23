# linediff

Compares two lists of lines and reports what changed.

## `diffLines(a: string[], b: string[]): DiffOp[]`

Returns the edit script that turns `a` into `b`, as a list of `{ op, line }` objects:

- `{ op: "keep", line }`: the line is in both lists,
- `{ op: "del", line }`: the line is only in `a` (it is removed),
- `{ op: "add", line }`: the line is only in `b` (it is inserted).

Lines are compared exactly, as whole strings. Reading the `keep` and `del` ops gives `a` again, reading the `keep`
and `add` ops gives `b`. The two input arrays are not modified.

The script is as short as possible: the kept lines are a longest common subsequence of `a` and `b`. When several
scripts are that short, the one returned is built from the front. While either list has lines left:

1. If the next line of `a` and the next line of `b` are equal, keep it and move on in both lists.
2. Otherwise delete the next line of `a` if the lines left in `a` after it still have as many lines in common with
   the lines left in `b` as the lines left in `a` including it have. If they would have fewer, insert the next
   line of `b` instead.

When `a` is used up, the remaining lines of `b` are inserted. When `b` is used up, the remaining lines of `a` are
deleted.

`diffLines(["x", "y"], ["y", "z"])` is `[del x, keep y, add z]`.

## `renderDiff(ops: DiffOp[]): string`

One line of text per op, joined with `"\n"` and without a trailing newline: two spaces and the line for `keep`,
`"- "` and the line for `del`, `"+ "` and the line for `add`. No ops give `""`.

## `diffStats(ops: DiffOp[]): { kept: number; deleted: number; added: number }`

How many ops of each kind there are.
