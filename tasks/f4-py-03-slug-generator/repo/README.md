# slugs

URL slugs for page titles.

## `slugify(text, max_length=60) -> str`

1. Letters are lower-cased and accented Latin letters lose their accents: `"Crème Brûlée"` becomes `"creme-brulee"`.
   Six letters have no accent form and are spelled out instead: `ß` is `ss`, `æ` is `ae`, `œ` is `oe`, `ø` is `o`,
   `ł` is `l` and `đ` is `d`.
2. Apostrophes (`'` and `’`) are dropped, not turned into hyphens: `"Don't Stop"` becomes `"dont-stop"`.
3. Every other run of characters that are not ASCII letters or digits becomes a single `-`, and leading and trailing
   hyphens are removed. Characters with no ASCII form (for example Japanese) count as separators.
4. The slug has at most `max_length` characters. A word that would be cut in the middle is left out completely,
   unless it is the first word, which is cut at `max_length`. The slug never ends with `-`.
5. If nothing is left the slug is `"untitled"` (shortened to `max_length` like any other slug).
6. A `max_length` below 1 raises `ValueError`.

## `unique_slug(text, taken, max_length=60) -> str`

The slug of `text`, made different from everything in `taken`. When the plain slug is taken, `-2`, `-3`, ... is
appended until the result is free. The number is always kept: the base slug is cut to make room for it (and a hyphen
left at the end of the cut is removed), so the result stays within `max_length`. A `max_length` below 8 raises
`ValueError`.
