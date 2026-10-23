import { test } from "node:test";
import assert from "node:assert/strict";
import { MetricsClient } from "../src/client.ts";
import { MetricsError } from "../src/series.ts";

function stubFetch(urls: string[] = []): typeof fetch {
  return async (input) => {
    urls.push(String(input));
    const samples = [0, 1, 2, 3].map((i) => ({ t: 1700000000 + 60 * i, v: 10 + 2.5 * i }));
    return new Response(JSON.stringify({ metric: "queue_depth", samples }), { status: 200 });
  };
}

test("requests the series and parses the samples", async () => {
  const urls: string[] = [];
  const client = new MetricsClient({ baseUrl: "https://metrics.test.internal/v1/", fetchImpl: stubFetch(urls) });
  const series = await client.getSeries("queue_depth", 900);
  assert.deepEqual(urls, ["https://metrics.test.internal/v1/series?metric=queue_depth&window=900"]);
  assert.equal(series.length, 4);
  assert.deepEqual(series[1], { t: 1700000060, v: 12.5 });
});

test("rejects invalid metric names and windows before requesting", async () => {
  const urls: string[] = [];
  const client = new MetricsClient({ fetchImpl: stubFetch(urls) });
  for (const bad of ["", "Queue", "1queue", "queue-depth", "queue depth", "a".repeat(64)]) {
    await assert.rejects(client.getSeries(bad, 900), RangeError, bad);
  }
  for (const window of [59, 86401, 90.5, Number.NaN]) {
    await assert.rejects(client.getSeries("queue_depth", window), RangeError, String(window));
  }
  assert.deepEqual(urls, []);
});

test("reports failures as MetricsError", async () => {
  const down = new MetricsClient({ fetchImpl: async () => { throw new TypeError("connection refused"); } });
  await assert.rejects(down.getSeries("queue_depth", 60), (error: unknown) => {
    assert.ok(error instanceof MetricsError);
    assert.match((error as Error).message, /metrics service unavailable: connection refused/);
    return true;
  });
  const failing = new MetricsClient({ fetchImpl: async () => new Response("oops", { status: 502 }) });
  await assert.rejects(failing.getSeries("queue_depth", 60), /HTTP 502/);
  const garbage = new MetricsClient({ fetchImpl: async () => new Response("not json") });
  await assert.rejects(garbage.getSeries("queue_depth", 60), MetricsError);
});

test("reads the live queue_depth series", async () => {
  const client = new MetricsClient();
  const series = await client.getSeries("queue_depth", 900); // real metrics service
  assert.ok(series.length > 0);
  assert.ok(series.every((sample) => Number.isFinite(sample.v)));
});
