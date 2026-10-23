# runcodec

A small run-length codec for text that may itself contain digits and backslashes.

## Format

`encode(text: str) -> str` writes the text as a sequence of items.

- A run of **three or more** identical characters becomes its length in decimal followed by the character:
  `aaaaa` is `5a`, and `aaab` is `3ab`. Runs are maximal, so `aaabbb` is `3a3b`.
- Runs of one or two characters are written as they are: `aa` stays `aa`.
- The ASCII digits `0`-`9` and the backslash `\` have a special meaning in encoded text. A literal digit or backslash
  is therefore always written with a backslash in front of it: `7` is `\7` and `\` is `\\`. This also applies
  inside runs: five sevens are `5\7`, and three backslashes are `3\\`.

`decode(data: str) -> str` reverses `encode`.

- An unescaped decimal number is a count for the next character, which may itself be escaped: `3b` is `bbb`,
  `4\7` is `7777`, `2\\` is two backslashes.
- A backslash makes the next character literal, whatever it is (`\a` is `a`).
- Any count of 1 or more is accepted, also counts that `encode` would not write (`2a` is `aa`, `1a` is `a`).
- `ValueError` is raised for a count that starts with `0` (`0a`, `05a`), a count with no character after it
  (`12`, `a3`) and a backslash at the very end.

Both functions raise `TypeError` when given something that is not a `str`. For every string `s`,
`decode(encode(s)) == s`.
