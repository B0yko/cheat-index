# Refreshing a configuration

Agents and models change monthly. This is the runbook for re-measuring one configuration when a new CLI version or
model ships, and for publishing it next to the existing rows.

## 1. Update the pinned version

Edit `images/agent-clis.txt` (one `package@version` per line), rebuild the images and check the setup:

```bash
uv run cheat-index images build
uv run cheat-index doctor
```

If the CLI changed its headless flags, update its adapter in `src/cheat_index/agents/` and the recorded stream in
`tests/fixtures/streams/`, and run `uv run pytest`.

## 2. Check the key and the budget

```bash
export OPENROUTER_API_KEY=...   # stays in the gateway container; agents never see it
uv run cheat-index doctor       # prints limit_remaining for the key, never the key
```

## 3. Run the configuration

```bash
uv run cheat-index run --agent opencode --model <openrouter model id> --tasks all --k 2 \
  --concurrency 4 --budget 15 --out runs --hardware "<your machine>" --yes
```

The run is resumable: re-running the same command skips finished runs and retries errored ones once. The command
prints its cost estimate before it starts; measured costs per run for the published configurations are in the
README's cost table.

## 4. Score, check and publish

```bash
uv run cheat-index score runs
uv run python scripts/publish_results.py runs --version <x.y.z>   # copies summaries into results/<version>/
uv run python scripts/check_generated.py                          # regenerates README tables, charts, leaderboard
```

Commit the summaries and regenerated files, attach the raw run archive to the release, and let the Pages workflow
rebuild the site.
