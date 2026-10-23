# 2. Hidden checks never enter an agent container

Status: accepted

## Context
If an agent can read the checks that score it, the benchmark measures how well it finds them. Bind mounts also
leak host paths and make it easy to expose more than intended.

## Decision
Agent containers receive a tar copy of the task's `repo/` directory and nothing else from the task (no bind
mounts). The hidden checks, `task.yaml`, `expected.yaml` and the scripted behaviours stay on the host. After the
agent stops, the runner copies `/work` out and starts a separate verification container with `--network none`,
into which it copies the final state, the pristine task and the hidden checks. Inside it, the visible tests run on
the final state as the agent left it; the hidden checks run on a copy in which every original test and test
configuration file is restored and test files the agent added are removed.

## Consequences
- An end-to-end test asserts that no hidden check file exists anywhere in an agent container's filesystem.
- Verification cannot be influenced by test files or configuration the agent changed, and it cannot reach any
  network (blocked-environment tasks stay blocked during verification).
