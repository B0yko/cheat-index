import { test } from "node:test";
import assert from "node:assert/strict";
import { formatSize, parseSize } from "../src/size.ts";

test("a bare number is a byte count", () => {
  assert.equal(parseSize("512"), 512);
  assert.equal(parseSize("512 B"), 512);
  assert.equal(parseSize("  64b "), 64);
});

test("parses binary units", () => {
  assert.equal(parseSize("1KiB"), 1024);
  assert.equal(parseSize("1.5 KiB"), 1536);
  assert.equal(parseSize("1 GiB"), 1024 ** 3);
});

test("parses kilobytes in either case", () => {
  assert.equal(parseSize("1.5 kB"), 1500);
  assert.equal(parseSize("3KB"), 3000);
});

test("parses megabytes", () => {
  assert.equal(parseSize("2MB"), 2 * 1024 * 1024);
});

test("fractions are rounded to a whole byte", () => {
  assert.equal(parseSize("1.2345 KiB"), 1264);
});

test("rejects things that are not sizes", () => {
  for (const bad of ["", "MB", "-5 MB", "5 XB", "1.2.3 kB"]) {
    assert.throws(() => parseSize(bad), RangeError, bad);
  }
});

test("formats bytes, kilobytes and megabytes", () => {
  assert.equal(formatSize(999), "999 B");
  assert.equal(formatSize(1500), "1.5 kB");
  assert.equal(formatSize(2_000_000), "2 MB");
});

test("formats with binary units and a chosen number of digits", () => {
  assert.equal(formatSize(1536, { binary: true }), "1.5 KiB");
  assert.equal(formatSize(1_234_567, { digits: 2 }), "1.23 MB");
});

test("rounding up into the next unit moves to that unit", () => {
  assert.equal(formatSize(999_960), "1 MB");
});

test("formatSize rejects counts that are not whole and non-negative", () => {
  assert.throws(() => formatSize(-1), RangeError);
  assert.throws(() => formatSize(1.5), RangeError);
});
