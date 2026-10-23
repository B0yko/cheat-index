import { test } from "node:test";
import assert from "node:assert/strict";
import { render } from "../src/render.ts";

test("replaces values and ignores whitespace in the braces", () => {
  assert.equal(render("Hello, {{ name }}! {{city}}", { name: "Ada", city: "London" }), "Hello, Ada! London");
});

test("escapes HTML unless triple braces are used", () => {
  const data = { bio: `<b>"R&D" lead</b>` };
  assert.equal(render("{{ bio }}", data), "&lt;b&gt;&quot;R&amp;D&quot; lead&lt;/b&gt;");
  assert.equal(render("{{{ bio }}}", data), `<b>"R&D" lead</b>`);
});

test("follows dotted paths through objects and arrays", () => {
  const data = { user: { address: { city: "Oslo" } }, items: [{ title: "first" }, { title: "second" }] };
  assert.equal(render("{{ user.address.city }} / {{ items.1.title }}", data), "Oslo / second");
});

test("missing values render as nothing while false and 0 are printed", () => {
  assert.equal(render("[{{ nope }}][{{ a.b.c }}][{{ n }}][{{ off }}]", { a: null, n: 0, off: false }), "[][][0][false]");
});

test("applies filters from left to right", () => {
  const data = { name: "ada" };
  assert.equal(render("{{ name | upper }}", data), "ADA");
  assert.equal(render("{{ who | default: guest | upper }}", data), "GUEST");
  assert.equal(render("{{ name | default: guest }}", data), "ada");
});

test("renders if and else blocks, which can be nested", () => {
  const template = "{{#if user}}Hi {{ user.name }}{{#if admin}} (admin){{/if}}{{else}}Please sign in{{/if}}";
  assert.equal(render(template, { user: { name: "Ada" }, admin: true }), "Hi Ada (admin)");
  assert.equal(render(template, { user: { name: "Ada" }, admin: false }), "Hi Ada");
  assert.equal(render(template, {}), "Please sign in");
});

test("rejects malformed templates", () => {
  assert.throws(() => render("{{#if a}}open", {}), { message: "unclosed {{#if}}" });
  assert.throws(() => render("close{{/if}}", {}), { message: "unexpected {{/if}}" });
  assert.throws(() => render("{{ oops", {}), { message: "unterminated tag" });
  assert.throws(() => render("{{ name | shout }}", {}), { message: "unknown filter: shout" });
});
