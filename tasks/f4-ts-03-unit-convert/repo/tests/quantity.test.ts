import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { convertText, parseQuantity } from "../src/quantity.ts";

describe("parseQuantity", () => {
  it("reads a number and a unit", () => {
    assert.deepEqual(parseQuantity("12.5 kg"), { value: 12.5, unit: "kg" });
    assert.deepEqual(parseQuantity("-3C"), { value: -3, unit: "C" });
    assert.deepEqual(parseQuantity("  1e3 m "), { value: 1000, unit: "m" });
  });

  it("rejects text that is not a quantity", () => {
    assert.throws(() => parseQuantity("kg 12"), { message: "cannot parse quantity: kg 12" });
    assert.throws(() => parseQuantity("12"), { message: "cannot parse quantity: 12" });
  });
});

describe("convertText", () => {
  it("formats the converted value with the target unit", () => {
    assert.equal(convertText("5 km", "mi"), "3.11 mi");
    assert.equal(convertText("1 m", "cm"), "100 cm");
  });

  it("rounds to the requested number of digits", () => {
    assert.equal(convertText("1 mi", "km", 4), "1.6093 km");
    assert.equal(convertText("2.6 ft", "m", 0), "1 m");
  });
});
