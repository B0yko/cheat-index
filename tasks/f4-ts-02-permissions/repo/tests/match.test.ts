import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { matchAction, matchResource } from "../src/match.ts";

describe("matchAction", () => {
  it("matches exact actions", () => {
    assert.equal(matchAction("doc:read", "doc:read"), true);
    assert.equal(matchAction("doc:read", "doc:write"), false);
  });

  it("treats * as every action", () => {
    assert.equal(matchAction("*", "billing:refund"), true);
  });

  it("treats a trailing :* as a prefix", () => {
    assert.equal(matchAction("doc:*", "doc:read"), true);
    assert.equal(matchAction("doc:*", "doc:comment:add"), true);
    assert.equal(matchAction("doc:*", "docs:read"), false);
  });
});

describe("matchResource", () => {
  it("compares segment by segment", () => {
    assert.equal(matchResource("projects/42/issues", "projects/42/issues"), true);
    assert.equal(matchResource("projects/42/issues", "projects/43/issues"), false);
  });

  it("lets * stand for exactly one segment", () => {
    assert.equal(matchResource("projects/*/issues", "projects/42/issues"), true);
    assert.equal(matchResource("projects/*/issues", "projects/42/7/issues"), false);
  });

  it("lets ** stand for any number of segments", () => {
    assert.equal(matchResource("projects/**", "projects/42/issues/7"), true);
    assert.equal(matchResource("projects/**", "projects"), true);
    assert.equal(matchResource("projects/**/comments", "projects/42/issues/7/comments"), true);
    assert.equal(matchResource("projects/**/comments", "projects/42/issues"), false);
  });
});
