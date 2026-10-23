import { test } from "node:test";
import assert from "node:assert/strict";
import { isTruthy, lookup } from "../src/lookup.ts";

test("finds values by dotted path", () => {
  const data = { a: { b: [10, 20] } };
  assert.equal(lookup(data, "a.b.1"), 20);
  assert.equal(lookup(data, "a.c"), undefined);
});

test("only looks at own properties", () => {
  assert.equal(lookup({}, "constructor"), undefined);
  assert.equal(lookup({ user: {} }, "user.__proto__"), undefined);
});

test("truthiness follows JavaScript except for empty arrays", () => {
  for (const value of [0, "", null, undefined, false, Number.NaN, []]) {
    assert.equal(isTruthy(value), false);
  }
  for (const value of ["0", {}, [0], 1, "no"]) {
    assert.equal(isTruthy(value), true);
  }
});
