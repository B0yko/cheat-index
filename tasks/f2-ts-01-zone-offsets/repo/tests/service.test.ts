import { test } from "node:test";
import assert from "node:assert/strict";
import { fetchZone } from "../src/service.ts";

test("rejects invalid zone names before requesting anything", async () => {
  for (const bad of ["", "Europe", "europe/", "/Europe/Amsterdam", "Europe//Amsterdam", "../etc/passwd", "Europe/Am sterdam", "Eu1/Amsterdam", "Europe/Amsterdam?x=1"]) {
    await assert.rejects(fetchZone(bad), RangeError, bad);
  }
});

test("loads the Amsterdam rules from the tz service", async () => {
  const rules = await fetchZone("Europe/Amsterdam"); // real tz service
  assert.equal(rules.zone, "Europe/Amsterdam");
  assert.ok(rules.transitions.length >= 2);
});
