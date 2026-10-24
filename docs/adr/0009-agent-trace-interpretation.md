# 9. How agent-trace/v1 is interpreted

Status: accepted

## Context
agent-trace/v1 is a small JSON Lines trace format (one trace per line: task, steps, claims, ground truth, meta)
that other tools can read, for example [proof-of-done](https://github.com/B0yko/proof-of-done). This repository
pins it as a JSON Schema, so interpretation choices must be explicit for traces to stay interchangeable.

## Decision
`schemas/agent-trace-v1.json` (JSON Schema draft 2020-12) encodes exactly the listed fields, types and enums; every
listed key is required except `ground_truth.details`; additional properties are allowed only under `meta` and inside
the free-form `args`, `output`, `subject` and `details` objects. Choices: `ts` must match RFC 3339; `name` and
`content` are string or null; `args`, `output` and `ok` may be null (messages have no tool input or result); step
`i` is 0-based. cheat-index traces: `task.domain` is `coding`; the first step is the instruction as a user message;
agent messages, tool calls and tool results follow in stream order with each `tool_result` directly after its
call; the last step is a `state_probe` named `hidden_checks`. Claim types are `tests_passed`, `done`, `fixed` and
`blocked` (this project's extension). `ground_truth.outcome` is `success` or `failure` from the hidden checks with
`checked_by: "state_probe"`. Detector findings, the claim class and the verdict flags go under `meta.cheat_index`.
Every trace is validated on write and on read; a round-trip test re-imports exported traces and re-scores them to
identical numbers.

## Consequences
- Exported traces can be re-judged by any tool that reads the format, for example
  `proof-of-done audit --source agent-trace traces.jsonl`.
