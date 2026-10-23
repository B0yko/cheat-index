import { test } from "node:test";
import assert from "node:assert/strict";
import { haversineKm, zoneFor } from "../src/geo.ts";

function close(actual: number, expected: number, tolerance = 0.01) {
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} is not within ${tolerance} of ${expected}`);
}

test("distance between known cities", () => {
  close(haversineKm({ lat: 52.3676, lng: 4.9041 }, { lat: 51.9244, lng: 4.4777 }), 57.229);
  close(haversineKm({ lat: 51.5074, lng: -0.1278 }, { lat: 48.8566, lng: 2.3522 }), 343.557);
});

test("distance is symmetric, zero for the same point and handles the antimeridian", () => {
  const a = { lat: 10, lng: 10 };
  assert.equal(haversineKm(a, a), 0);
  const b = { lat: 20, lng: 30 };
  assert.equal(haversineKm(a, b), haversineKm(b, a));
  close(haversineKm({ lat: 0, lng: 179.5 }, { lat: 0, lng: -179.5 }), 111.195);
});

test("rejects impossible coordinates", () => {
  assert.throws(() => haversineKm({ lat: 91, lng: 0 }, { lat: 0, lng: 0 }), RangeError);
  assert.throws(() => haversineKm({ lat: 0, lng: 0 }, { lat: 0, lng: 181 }), RangeError);
  assert.throws(() => haversineKm({ lat: Number.NaN, lng: 0 }, { lat: 0, lng: 0 }), RangeError);
});

test("zone bands include their upper bound", () => {
  assert.deepEqual(
    [0, 25, 25.01, 100, 100.5, 400, 400.1, 1000, 1000.1, 20000].map(zoneFor),
    ["A", "A", "B", "B", "C", "C", "D", "D", "E", "E"],
  );
});

test("zoneFor rejects bad distances", () => {
  for (const bad of [-1, Number.NaN, Infinity]) assert.throws(() => zoneFor(bad), RangeError);
});
