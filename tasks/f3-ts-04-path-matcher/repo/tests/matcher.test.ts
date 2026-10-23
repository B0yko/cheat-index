import { test } from "node:test";
import assert from "node:assert/strict";
import { PathMatcher } from "../src/matcher.ts";

test("star stays inside one folder level", () => {
  const matcher = new PathMatcher(["assets/*.png"]);
  assert.equal(matcher.matches("assets/logo.png"), true);
  assert.equal(matcher.matches("assets/icons/logo.png"), false);
});

test("double star crosses folders", () => {
  const matcher = new PathMatcher(["services/**/handler.ts"]);
  assert.equal(matcher.matches("services/billing/v2/handler.ts"), true);
  assert.equal(matcher.matches("services/handler.ts"), true);
});

test("later patterns override earlier ones", () => {
  const matcher = new PathMatcher(["docs/**", "!docs/drafts/**", "docs/drafts/final-*.md"]);
  const paths = ["docs/intro.md", "docs/drafts/idea.md", "docs/drafts/final-v3.md", "src/main.ts"];
  assert.deepEqual(matcher.filter(paths), ["docs/intro.md", "docs/drafts/final-v3.md"]);
});
