import { test } from "node:test";
import assert from "node:assert/strict";
import { evaluateRule, findIncidents } from "../src/rules.ts";

const series = (values: number[]) => values.map((v, i) => ({ t: 1000 + 60 * i, v }));
const rule = { threshold: 10, above: true, forSeconds: 120 };

test("ok when the last sample does not breach", () => {
  assert.deepEqual(evaluateRule(series([20, 30, 5]), rule), { state: "ok", since: null, value: 5 });
  assert.deepEqual(evaluateRule(series([10, 10]), rule), { state: "ok", since: null, value: 10 });
  assert.deepEqual(evaluateRule([], rule), { state: "ok", since: null, value: null });
});

test("pending until the breach has lasted long enough", () => {
  assert.deepEqual(evaluateRule(series([5, 11]), rule), { state: "pending", since: 1060, value: 11 });
  assert.deepEqual(evaluateRule(series([5, 11, 12]), rule), { state: "pending", since: 1060, value: 12 });
  assert.deepEqual(evaluateRule(series([5, 11, 12, 13]), rule), { state: "firing", since: 1060, value: 13 });
});

test("only the trailing run counts and below-rules work", () => {
  assert.deepEqual(evaluateRule(series([11, 12, 13, 5, 11]), rule), { state: "pending", since: 1240, value: 11 });
  const low = { threshold: 5, above: false, forSeconds: 0 };
  assert.deepEqual(evaluateRule(series([9, 4]), low), { state: "firing", since: 1060, value: 4 });
  assert.deepEqual(evaluateRule(series([9, 5]), low), { state: "ok", since: null, value: 5 });
});

test("finds incidents with their peak", () => {
  const values = [1, 12, 15, 13, 2, 11, 3, 14, 20, 11];
  assert.deepEqual(findIncidents(series(values), rule), [
    { from: 1060, to: 1180, peak: 15 },
    { from: 1420, to: 1540, peak: 20 },
  ]);
  assert.deepEqual(findIncidents(series(values), { ...rule, forSeconds: 0 }).length, 3);
});

test("below-rules report the lowest value as the peak", () => {
  const low = { threshold: 5, above: false, forSeconds: 60 };
  assert.deepEqual(findIncidents(series([9, 4, 2, 3, 9]), low), [{ from: 1060, to: 1180, peak: 2 }]);
});

test("rejects invalid rules", () => {
  for (const bad of [{ threshold: Number.NaN, above: true, forSeconds: 0 }, { threshold: 1, above: true, forSeconds: -1 }, { threshold: 1, above: true, forSeconds: 1.5 }]) {
    assert.throws(() => evaluateRule([], bad), RangeError);
    assert.throws(() => findIncidents([], bad), RangeError);
  }
});
