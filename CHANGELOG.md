# Changelog

## 0.1.0 (2026-10-24)

First release of the Agent Cheat Index.

- 40 tasks (24 Python, 16 TypeScript) in four families: contradictory specification, blocked environment,
  tempting shortcut, control; each with hidden checks, one honest and at least two cheating scripted behaviours.
- Runner: Claude Code, Codex CLI, OpenCode and GitHub Copilot CLI adapters plus a scripted replay agent; per-run
  internal network with an allow-listing egress proxy; key-holding model gateway with per-run cost caps; network-less
  verification container; cost ledger, resumable runs, one retry for errored runs.
- Nine deterministic detectors, a rule-based final-message classifier, verdict flags and the Agent Cheat Index with
  task-cluster bootstrap intervals, Wilson intervals, rank groups and a paired ordering rule.
- Labelled sets: 358 authored and 244 frozen held-out detector cases; 120 authored and 80 frozen held-out final
  messages; detector release gates.
- Published results in `results/v0.1.0/`, raw runs as a release asset, static leaderboard site, agent-trace/v1
  export, `demo` with bundled real runs.
