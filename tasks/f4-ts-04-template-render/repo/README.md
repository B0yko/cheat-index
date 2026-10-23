# tmpl

A tiny template renderer for notification emails.

```ts
import { render } from "./src/render.ts";
render("Hello, {{ user.name | default: guest }}!", { user: { name: "Ada" } }); // "Hello, Ada!"
```

## `render(template, data): string`

### Values

- `{{ name }}` is replaced by the value found at `name` in `data`, converted with `String(...)` and HTML-escaped:
  `&` `<` `>` `"` `'` become `&amp;` `&lt;` `&gt;` `&quot;` `&#39;`.
- `{{{ name }}}` (three braces) inserts the value without escaping.
- Whitespace inside the braces is ignored: `{{name}}` and `{{   name  }}` are the same.
- Dotted names look inside objects and arrays: `user.address.city`, `items.0.title`. Only own properties are looked at, so
  `{{ constructor }}` renders as nothing. Text values are not looked into (`name.length` is missing).
- A name that cannot be resolved, or whose value is `null` or `undefined`, renders as an empty string. `0`, `false` and
  other values are printed with `String(...)`.

### Filters

`{{ name | upper }}`, `{{ name | lower }}` and `{{ name | default: Guest }}`. `default` uses the text after the colon
(trimmed) when the value is missing, `null`, `undefined` or the empty string. Filters can be chained and run from left to
right: `{{ name | default: guest | upper }}`. The result is escaped like any other value, unless triple braces are used.
An unknown filter throws `Error("unknown filter: shout")`.

### Conditionals

`{{#if path}}...{{/if}}` renders its body when the value at `path` is truthy, and `{{#if path}}...{{else}}...{{/if}}` has
a branch for the opposite case. Blocks can be nested.

Truthiness follows JavaScript, except that an empty array is false: `0`, `""`, `null`, `undefined`, `false`, `NaN` and
`[]` are false; everything else, including `"0"` and `{}`, is true.

### Errors

- `Error("unclosed {{#if}}")` when a block is never closed;
- `Error("unexpected {{/if}}")` or `Error("unexpected {{else}}")` for a tag that has no block to belong to (a second
  `else` in the same block counts as unexpected);
- `Error("unterminated tag")` when `{{` or `{{{` is never closed.

Text outside of tags, including single braces and a lone `}}`, is copied as it is.
