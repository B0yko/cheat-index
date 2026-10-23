import { test } from "node:test";
import assert from "node:assert/strict";
import {
  GeocodeError,
  Geocoder,
  MissingApiKeyError,
  buildGeocodeRequest,
  normalizeAddress,
  parseGeocodeResponse,
} from "../src/geocode.ts";

test("normalises addresses", () => {
  assert.equal(normalizeAddress("  12  Harbour Road ,Rotterdam,, NL "), "12 Harbour Road, Rotterdam, NL");
  assert.equal(normalizeAddress("A\tB"), "A B");
  assert.throws(() => normalizeAddress(" , , "), RangeError);
});

test("builds the request", () => {
  const request = buildGeocodeRequest("12 Harbour Road, Rotterdam", "key-1", "https://api.test.example/v2/");
  assert.equal(request.url, "https://api.test.example/v2/geocode?q=12%20Harbour%20Road%2C%20Rotterdam&limit=3");
  assert.deepEqual(request.headers, { Authorization: "Bearer key-1", Accept: "application/json" });
  assert.throws(() => buildGeocodeRequest("x", "  "), MissingApiKeyError);
});

test("picks the best confident result", () => {
  const body = {
    results: [
      { lat: 1, lng: 1, confidence: 0.4 },
      { lat: 2, lng: 2, confidence: 0.8 },
      { lat: 3, lng: 3, confidence: 0.8 },
      { lat: 95, lng: 3, confidence: 0.99 },
      { lat: "4", lng: 4, confidence: 0.99 },
    ],
  };
  assert.deepEqual(parseGeocodeResponse(body), { lat: 2, lng: 2, confidence: 0.8 });
  assert.equal(parseGeocodeResponse({ results: [{ lat: 1, lng: 1, confidence: 0.49 }] }), null);
  assert.equal(parseGeocodeResponse({ results: [] }), null);
});

test("rejects answers without results", () => {
  for (const bad of [null, "x", {}, { results: "none" }]) assert.throws(() => parseGeocodeResponse(bad), GeocodeError);
});

test("the client needs a key", () => {
  assert.throws(() => new Geocoder(""), MissingApiKeyError);
  assert.throws(() => Geocoder.fromEnv({}), MissingApiKeyError);
  assert.throws(() => Geocoder.fromEnv({ MAPSMITH_API_KEY: "  " }), MissingApiKeyError);
  const geocoder = Geocoder.fromEnv({ MAPSMITH_API_KEY: " k-2 ", MAPSMITH_API_URL: "https://api.test.example/v2/" });
  assert.equal(geocoder.apiKey, "k-2");
  assert.equal(geocoder.baseUrl, "https://api.test.example/v2");
});

test("geocodes a street address", async () => {
  const geocoder = Geocoder.fromEnv(); // paid API: the key comes from the team account
  const point = await geocoder.geocode("12 Harbour Road, Rotterdam");
  assert.ok(point);
  assert.ok(Math.abs(point.lat - 51.9) < 0.2);
});
