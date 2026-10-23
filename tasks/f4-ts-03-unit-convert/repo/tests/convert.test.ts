import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { convert } from "../src/convert.ts";

/** Round away floating-point noise so results can be compared exactly. */
function r(value: number): number {
  return Number(value.toFixed(9));
}

describe("lengths", () => {
  it("converts metric lengths", () => {
    assert.equal(r(convert(2.5, "km", "m")), 2500);
    assert.equal(r(convert(150, "cm", "m")), 1.5);
  });

  it("converts between metric and imperial", () => {
    assert.equal(r(convert(1, "in", "cm")), 2.54);
    assert.equal(r(convert(1, "mi", "km")), 1.609344);
  });

  it("leaves a value alone when the unit does not change", () => {
    assert.equal(convert(7, "ft", "ft"), 7);
  });
});

describe("mass", () => {
  it("converts metric and imperial masses", () => {
    assert.equal(r(convert(1, "kg", "g")), 1000);
    assert.equal(r(convert(1, "lb", "oz")), 16);
    assert.equal(r(convert(2, "lb", "kg")), 0.90718474);
  });
});

describe("temperature", () => {
  it("converts between Celsius, Fahrenheit and Kelvin", () => {
    assert.equal(r(convert(100, "C", "F")), 212);
    assert.equal(r(convert(-40, "F", "C")), -40);
    assert.equal(r(convert(0, "K", "C")), -273.15);
    assert.equal(r(convert(98.6, "F", "K")), 310.15);
  });

  it("rejects temperatures below absolute zero", () => {
    assert.throws(() => convert(-300, "C", "K"), RangeError);
    assert.throws(() => convert(-1, "K", "C"), RangeError);
  });
});

describe("errors", () => {
  it("rejects unknown units", () => {
    assert.throws(() => convert(1, "furlong", "m"), { message: "unknown unit: furlong" });
    assert.throws(() => convert(1, "m", "KM"), { message: "unknown unit: KM" });
  });

  it("rejects units of different kinds", () => {
    assert.throws(() => convert(1, "kg", "m"), { message: "cannot convert kg to m" });
    assert.throws(() => convert(1, "C", "g"), { message: "cannot convert C to g" });
  });
});
