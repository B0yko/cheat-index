import { test } from "node:test";
import assert from "node:assert/strict";
import { parseQuery } from "../src/query.ts";

test("parses simple pairs", () => {
  assert.deepEqual(parseQuery("?color=blue&count=3"), { color: "blue", count: "3" });
});

test("decodes plus and percent escapes", () => {
  assert.deepEqual(parseQuery("name=Ada+Lovelace&city=Z%C3%BCrich"), { name: "Ada Lovelace", city: "Zürich" });
});

test("collects repeated keys", () => {
  assert.deepEqual(parseQuery("tag=a&tag=b&tag=c"), { tag: ["a", "b", "c"] });
});
