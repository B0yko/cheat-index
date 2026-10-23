# 4. Every published row goes through OpenRouter; no subscription logins

Status: accepted

## Context
Consumer subscriptions (Claude, ChatGPT, Cursor) are licensed to people, not to automated harnesses, and their
terms restrict automated access. A benchmark also needs one billing and accounting path for every row.

## Decision
All models for published rows are called through OpenRouter with an API key. The key lives only in the model
gateway container (`runner/model_gateway.py`). Agents receive a per-run random token and a plain-HTTP base URL; the
gateway maps the token to its run, swaps in the real key, records usage and cost from the responses, reconciles
exact costs through `GET /api/v1/generation`, and refuses further requests once the run's token or cost cap, or the
global budget, is reached. Tokens are revoked when the run ends, so they are useless anywhere else.

## Consequences
- Vendor-key rows (for example Gemini CLI or Cursor CLI) are possible later but are labelled "vendor key, not
  OpenRouter" and are not part of v0.1.
- Client-side budget flags are not relied on: Claude Code's `--max-budget-usd` prices OpenRouter model ids with its
  own table and stops runs early, so the gateway enforces budgets instead.
