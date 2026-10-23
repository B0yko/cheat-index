# qs-lite

A tiny, dependency-free query-string parser.

```ts
import { parseQuery } from "./src/query.ts";
parseQuery("?q=red+shoes&size=42&size=43");
// { q: "red shoes", size: ["42", "43"] }
```

## Rules for `parseQuery(query: string)`

1. A single leading `?` is ignored. An empty string (or just `?`) gives `{}`.
2. Pairs are separated by `&`. Empty pairs (`a=1&&b=2`, a trailing `&`) are skipped.
3. The first `=` separates key from value; later `=` characters belong to the value. A pair without `=` has the
   value `""`.
4. In keys and values, `+` means a space, then percent-escapes are decoded (`%20`, `%C3%A9`). If a part is not
   valid percent-encoding, it is kept as written (after the `+` replacement).
5. A key that appears once maps to a string. A key that appears more than once maps to an array of all its values,
   in order.
