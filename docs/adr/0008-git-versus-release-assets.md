# 8. What goes into git and what goes into release assets

Status: accepted

## Context
Raw runs are large (streams, diffs, proxy logs) and the README, site and CI must be regenerable from what is in the
repository.

## Decision
Committed under `results/v0.1.0/`: one summary per run (configuration, versions, task and content hash, verdict
flags, detector findings with short evidence excerpts, final message, hidden-check result, cost, tokens, wall time)
plus the detector and classifier quality report. Attached to the GitHub Release as one compressed archive: every
run directory (raw stream, stderr, final diff, changes, proxy log, verification output, gateway usage log), after a
scan for secrets, host names and absolute paths. `scripts/check_generated.py --check` runs in CI and fails when the
README tables, charts or site differ from what the committed summaries produce.

## Consequences
- Every published number can be recomputed from git alone; every verdict can be re-derived from the release asset
  (`cheat-index verify RUN_DIR`).
