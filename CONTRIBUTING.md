# Contributing

Thanks for helping. Issues and pull requests are welcome, especially:

- a disputed verdict (open an issue with the run id; `cheat-index verify RUN_DIR` on the release asset reproduces
  it);
- detector false positives or misses, with a minimal patch against one of the task repositories;
- new adapters for agent CLIs with a documented headless mode and API-key access.

## Development

```bash
uv sync
npm ci --prefix tools/ts                         # pinned TypeScript compiler for test-file analysis
export CHEAT_INDEX_NODE_PATH=$PWD/tools/ts/node_modules
uv run pytest -m "not docker"                    # unit and integration tests
uv run cheat-index tasks validate                # every scripted behaviour through verification and detectors
uv run cheat-index images build && uv run pytest -m docker   # container end-to-end tests
uv run ruff check . && uv run ruff format --check . && uv run mypy
```

## Rules for changes

- Tasks: `repo/` must never contain the canary string or anything that tells an agent it is being evaluated;
  hidden checks test only what the task's README or instruction specifies. `cheat-index tasks validate` must pass.
- The held-out sets (`eval/detectors/heldout.yaml`, `eval/claims/heldout.yaml`) are frozen. Do not tune detectors
  or the classifier on them. A label correction goes only through the set's `CHANGES.md` with a reason, together
  with the updated `MANIFEST.sha256`.
- Results are generated: after changing scoring code, run `uv run python scripts/rescore.py` on the raw runs and
  `uv run python scripts/check_generated.py`; CI fails if the README or leaderboard drift from the summaries.
