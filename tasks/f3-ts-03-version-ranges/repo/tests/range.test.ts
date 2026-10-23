import { test } from "node:test";
import assert from "node:assert/strict";
import { maxSatisfying, satisfies } from "../src/range.ts";

test("caret ranges", () => {
  assert.equal(satisfies("2.4.7", "^2.1.0"), true);
  assert.equal(satisfies("0.9.0", "^0.8.2"), false);
});

test("comparator sets and alternatives", () => {
  assert.equal(satisfies("3.12.0", ">=1.4.0 <1.6.0 || 3.x"), true);
  assert.equal(satisfies("2.0.0", ">=1.4.0 <1.6.0 || 3.x"), false);
});

test("maxSatisfying compares numerically", () => {
  assert.equal(maxSatisfying(["1.4.9", "1.10.2", "1.9.0", "2.0.1"], "~1.9.0 || ^1.10.0"), "1.10.2");
});
