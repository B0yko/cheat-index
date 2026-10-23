import { test } from "node:test";
import assert from "node:assert/strict";
import { diffLines, diffStats, renderDiff } from "../src/diff.ts";

test("keeps common lines and marks the rest", () => {
  const ops = diffLines(["gateway", "relay", "mirror"], ["gateway", "proxy", "mirror", "tunnel"]);
  assert.deepEqual(ops, [
    { op: "keep", line: "gateway" },
    { op: "del", line: "relay" },
    { op: "add", line: "proxy" },
    { op: "keep", line: "mirror" },
    { op: "add", line: "tunnel" },
  ]);
});

test("renders a plain-text diff", () => {
  const ops = diffLines(["north", "south"], ["north", "east", "south"]);
  assert.equal(renderDiff(ops), "  north\n+ east\n  south");
});

test("counts the changes", () => {
  const ops = diffLines(["a1", "b2", "c3", "d4"], ["b2", "d4", "e5"]);
  assert.deepEqual(diffStats(ops), { kept: 2, deleted: 2, added: 1 });
});
