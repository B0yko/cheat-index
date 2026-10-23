import { test } from "node:test";
import assert from "node:assert/strict";
import { MetricsError, parseSeries } from "../src/series.ts";

test("parses samples in order", () => {
  const body = { metric: "queue_depth", samples: [{ t: 100, v: 1.5 }, { t: 160, v: -2 }, { t: 220, v: 0 }] };
  assert.deepEqual(parseSeries(body), [{ t: 100, v: 1.5 }, { t: 160, v: -2 }, { t: 220, v: 0 }]);
  assert.deepEqual(parseSeries({ samples: [] }), []);
});

test("rejects malformed answers", () => {
  const bad: unknown[] = [
    null,
    {},
    { samples: "x" },
    { samples: [null] },
    { samples: [{ t: -1, v: 1 }] },
    { samples: [{ t: 1.5, v: 1 }] },
    { samples: [{ t: "1", v: 1 }] },
    { samples: [{ t: 1, v: "1" }] },
    { samples: [{ t: 1, v: null }] },
    { samples: [{ t: 1, v: Number.NaN }] },
    { samples: [{ t: 5, v: 1 }, { t: 5, v: 2 }] },
    { samples: [{ t: 5, v: 1 }, { t: 4, v: 2 }] },
  ];
  for (const body of bad) assert.throws(() => parseSeries(body), MetricsError);
});
