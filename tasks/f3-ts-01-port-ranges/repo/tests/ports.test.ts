import { test } from "node:test";
import assert from "node:assert/strict";
import { countPorts, normalizePorts, parsePorts } from "../src/ports.ts";

test("merges overlapping and touching ranges", () => {
  assert.equal(normalizePorts("9090,9092-9095, 2222, 9091,9096"), "2222,9090-9096");
});

test("counts distinct ports", () => {
  assert.equal(countPorts("3000-3009,3005-3014,7000"), 16);
});

test("rejects ports outside 1-65535", () => {
  assert.throws(() => parsePorts("70000"));
});
