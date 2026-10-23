import { test } from "node:test";
import assert from "node:assert/strict";
import { ZoneError, formatOffset, offsetAt, parseZone, toLocalIso, type ZoneRules } from "../src/zone.ts";

const amsterdam: ZoneRules = {
  zone: "Europe/Amsterdam",
  initial: { offsetMinutes: 60, abbr: "CET" },
  transitions: [
    { at: "2026-03-29T01:00:00Z", offsetMinutes: 120, abbr: "CEST" },
    { at: "2026-10-25T01:00:00Z", offsetMinutes: 60, abbr: "CET" },
  ],
};

test("offset in force at an instant", () => {
  assert.deepEqual(offsetAt(amsterdam, "2026-01-15T12:00:00Z"), { offsetMinutes: 60, abbr: "CET" });
  assert.deepEqual(offsetAt(amsterdam, "2026-03-29T00:59:59Z"), { offsetMinutes: 60, abbr: "CET" });
  assert.deepEqual(offsetAt(amsterdam, "2026-03-29T01:00:00Z"), { offsetMinutes: 120, abbr: "CEST" });
  assert.deepEqual(offsetAt(amsterdam, "2026-07-01T00:00:00Z"), { offsetMinutes: 120, abbr: "CEST" });
  assert.deepEqual(offsetAt(amsterdam, "2026-10-25T01:00:00Z"), { offsetMinutes: 60, abbr: "CET" });
});

test("formats offsets", () => {
  assert.equal(formatOffset(0), "+00:00");
  assert.equal(formatOffset(60), "+01:00");
  assert.equal(formatOffset(-330), "-05:30");
  assert.equal(formatOffset(345), "+05:45");
});

test("converts to local time, rolling the date over", () => {
  assert.equal(toLocalIso("2026-03-29T00:59:59Z", amsterdam), "2026-03-29T01:59:59+01:00");
  assert.equal(toLocalIso("2026-03-29T01:00:00Z", amsterdam), "2026-03-29T03:00:00+02:00");
  assert.equal(toLocalIso("2026-12-31T23:30:00Z", amsterdam), "2027-01-01T00:30:00+01:00");
  const newfoundland: ZoneRules = { zone: "America/St_Johns", initial: { offsetMinutes: -210, abbr: "NST" }, transitions: [] };
  assert.equal(toLocalIso("2026-01-01T02:00:00Z", newfoundland), "2025-12-31T22:30:00-03:30");
});

test("rejects invalid instants", () => {
  for (const bad of ["2026-02-30T00:00:00Z", "2026-03-29T24:00:00Z", "2026-03-29 01:00:00Z", "2026-03-29T01:00:00", "2026-03-29T01:00:00.000Z", "2026-03-29T01:00:00+01:00", ""]) {
    assert.throws(() => offsetAt(amsterdam, bad), RangeError, bad);
    assert.throws(() => toLocalIso(bad, amsterdam), RangeError, bad);
  }
});

test("parses a service answer", () => {
  const body = {
    zone: "Europe/Amsterdam",
    initial: { offset_minutes: 60, abbr: "CET" },
    transitions: [
      { at: "2026-03-29T01:00:00Z", offset_minutes: 120, abbr: "CEST" },
      { at: "2026-10-25T01:00:00Z", offset_minutes: 60, abbr: "CET" },
    ],
  };
  assert.deepEqual(parseZone(body), amsterdam);
});

test("rejects malformed answers", () => {
  const ok = { zone: "Z/Z", initial: { offset_minutes: 0, abbr: "UTC" }, transitions: [] as unknown[] };
  assert.doesNotThrow(() => parseZone(ok));
  const t1 = { at: "2026-03-29T01:00:00Z", offset_minutes: 120, abbr: "CEST" };
  const bad: unknown[] = [
    null,
    { ...ok, zone: 5 },
    { ...ok, initial: undefined },
    { ...ok, initial: { offset_minutes: 841, abbr: "X" } },
    { ...ok, initial: { offset_minutes: -721, abbr: "X" } },
    { ...ok, initial: { offset_minutes: 30.5, abbr: "X" } },
    { ...ok, initial: { offset_minutes: 0, abbr: "" } },
    { ...ok, initial: { offset_minutes: 0, abbr: "TOOLONG" } },
    { ...ok, transitions: "none" },
    { ...ok, transitions: [{ ...t1, at: "2026-03-29" }] },
    { ...ok, transitions: [t1, t1] },
    { ...ok, transitions: [t1, { ...t1, at: "2026-01-01T00:00:00Z" }] },
  ];
  for (const body of bad) assert.throws(() => parseZone(body), ZoneError);
});
