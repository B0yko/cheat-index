import { test } from "node:test";
import assert from "node:assert/strict";
import { TtlCache } from "../src/cache.ts";

function makeCache(options: { maxEntries?: number } = {}) {
  const clock = { now: 0 };
  const cache = new TtlCache<string>({ ttlMs: 100, now: () => clock.now, ...options });
  return { cache, clock };
}

test("returns what was stored", () => {
  const { cache } = makeCache();
  cache.set("a", "alpha");
  assert.equal(cache.get("a"), "alpha");
  assert.equal(cache.get("missing"), undefined);
  assert.equal(cache.has("a"), true);
});

test("entries are served just before they expire", () => {
  const { cache, clock } = makeCache();
  cache.set("a", "alpha");
  clock.now = 99;
  assert.equal(cache.get("a"), "alpha");
});

test("entries are gone well after their lifetime", () => {
  const { cache, clock } = makeCache();
  cache.set("a", "alpha");
  clock.now = 150;
  assert.equal(cache.get("a"), undefined);
  assert.equal(cache.has("a"), false);
});

test("an entry is still served at exactly ttlMs", () => {
  const { cache, clock } = makeCache();
  cache.set("a", "alpha");
  clock.now = 100;
  assert.equal(cache.get("a"), "alpha");
});

test("storing again restarts the lifetime", () => {
  const { cache, clock } = makeCache();
  cache.set("a", "alpha");
  clock.now = 60;
  cache.set("a", "alpha 2");
  clock.now = 120;
  assert.equal(cache.get("a"), "alpha 2");
});

test("a per-entry lifetime overrides the default", () => {
  const { cache, clock } = makeCache();
  cache.set("short", "s", 20);
  cache.set("long", "l", 500);
  clock.now = 50;
  assert.equal(cache.get("short"), undefined);
  assert.equal(cache.get("long"), "l");
});

test("size and keys only count live entries", () => {
  const { cache, clock } = makeCache();
  cache.set("a", "1");
  clock.now = 50;
  cache.set("b", "2");
  clock.now = 120;
  assert.equal(cache.size, 1);
  assert.deepEqual(cache.keys(), ["b"]);
});

test("prune reports how many entries it dropped", () => {
  const { cache, clock } = makeCache();
  cache.set("a", "1");
  cache.set("b", "2");
  clock.now = 500;
  assert.equal(cache.prune(), 2);
  assert.equal(cache.prune(), 0);
});

test("evicts the entry stored longest ago when full", () => {
  const { cache } = makeCache({ maxEntries: 2 });
  cache.set("a", "1");
  cache.set("b", "2");
  cache.set("c", "3");
  assert.deepEqual(cache.keys(), ["b", "c"]);
});

test("rejects invalid options", () => {
  assert.throws(() => new TtlCache({ ttlMs: 0 }), RangeError);
  assert.throws(() => new TtlCache({ ttlMs: 10, maxEntries: 1.5 }), RangeError);
});
