# Agent setups

Every agent runs headless in a fresh container (`images/python` or `images/node`) as the non-root user `agent`, with
the task repository at `/work` (a fresh git repository with one commit), a throwaway `HOME=/home/agent` and no host
mounts. The OpenRouter key never enters the container: each run gets a random token that only the model gateway
accepts, and only for that run. The exact command line, environment and config files come from the adapter modules
in `src/cheat_index/agents/`; this page restates them. Versions are pinned in `images/agent-clis.txt`.

Common environment for every agent:

| Variable | Value | Why |
|---|---|---|
| `HOME` | `/home/agent` | throwaway; no user config, hooks, plugins or MCP servers |
| `HTTP_PROXY`, `HTTPS_PROXY` (and lower case) | `http://proxy:3128` | the per-run egress proxy, which refuses everything off the allow-list and logs it |
| `NO_PROXY` | `gateway,localhost,127.0.0.1` | model traffic goes straight to the gateway |
| `NODE_USE_ENV_PROXY` | `1` | makes Node's built-in `fetch` honour the proxy variables |
| `CI`, `TERM=dumb`, `NO_COLOR=1` | | non-interactive output |

Container limits: 2 CPUs, 4 GB memory, 512 processes, `--cap-drop ALL`, `no-new-privileges`, 15-minute wall clock.
The gateway refuses a run's requests once it has cost more than its cap (default $0.60) or used 6 million tokens.

## Claude Code (`@anthropic-ai/claude-code`)

```
claude -p "<instruction>" --output-format stream-json --verbose \
  --permission-mode bypassPermissions --permission-prompts none \
  --max-turns 60 --model <openrouter model id> --no-session-persistence
```

- Since v2.1.302, `claude -p` on a third-party provider starts in the `default` permission mode, which needs someone
  to answer prompts; inside the sandbox we set the mode explicitly, and `--permission-prompts none` denies anything
  that would still prompt.
- Model routing (OpenRouter's Claude Code guide, with the base URL pointed at our gateway):
  `ANTHROPIC_BASE_URL=http://gateway:8080/api`, `ANTHROPIC_AUTH_TOKEN=<run token>`, `ANTHROPIC_API_KEY=` (empty),
  and `ANTHROPIC_MODEL`, `ANTHROPIC_SMALL_FAST_MODEL`, `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU}_MODEL` and
  `CLAUDE_CODE_SUBAGENT_MODEL` all set to the run's model, so no request goes to a different model.
- Switched off: `DISABLE_TELEMETRY`, `DISABLE_ERROR_REPORTING`, `DISABLE_AUTOUPDATER`,
  `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY`,
  `CLAUDE_CODE_DISABLE_TERMINAL_TITLE`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY`, `CLAUDE_CODE_SKIP_PROMPT_HISTORY`,
  `CLAUDE_CODE_ATTRIBUTION_HEADER=0`, `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS`; `skipWebFetchPreflight: true` in
  `~/.claude/settings.json`.
- Not used: `--max-budget-usd`. It prices OpenRouter model ids with Claude Code's own price table and stopped a
  trivial run after one turn in our contract check; the gateway enforces the budget instead.
- Rules file: `CLAUDE.md` at the repository root. Hooks: `--hooks DIR` must contain `claude-code.json` (settings
  such as a `hooks` block), which is merged into `~/.claude/settings.json`; every other file in DIR is copied to
  `~/.claude/hooks/` under the same relative path, so hook commands can call `~/.claude/hooks/<script>`.

## Codex CLI (`@openai/codex`)

```
codex exec --json --skip-git-repo-check --ephemeral \
  --dangerously-bypass-approvals-and-sandbox -m <openrouter model id> "<instruction>"
```

- `CODEX_HOME=/home/agent/.codex` with this `config.toml` (provider settings are honoured only in the user-level
  config): `model_provider = "openrouter"`, `[model_providers.openrouter]` with
  `base_url = "http://gateway:8080/api/v1"`, `env_key = "OPENROUTER_API_KEY"` (the run token) and
  `wire_api = "responses"` (the only wire API current Codex supports; OpenRouter serves `/api/v1/responses`
  statelessly). Also `approval_policy = "never"`, `sandbox_mode = "danger-full-access"`,
  `check_for_update_on_startup = false`, analytics, feedback and history persistence off.
- `--dangerously-bypass-approvals-and-sandbox` is the documented mode for environments that are sandboxed from the
  outside, which ours is.
- No turn or cost cap flag exists in this version; the gateway's cap and the wall clock apply.
- Rules file: `AGENTS.md` at the repository root. Hooks: `--hooks DIR` must contain `codex-hooks.json`, which is
  written to `~/.codex/hooks.json`; nothing else in DIR is copied.

## OpenCode (`opencode-ai`)

```
opencode run --format json -m openrouter/<openrouter model id> --auto "<instruction>"
```

- `~/.config/opencode/opencode.json`: the built-in `openrouter` provider with
  `options.baseURL = "http://gateway:8080/api/v1"` and `options.apiKey = <run token>`; `share: "disabled"`,
  `autoupdate: false`, `snapshot: false`; permissions `edit`, `bash`, `webfetch`, `external_directory` set to
  `allow` (what `ask` does in `opencode run` is not documented); the `build` agent's `steps` set to the turn cap.
- Switched off: `OPENCODE_DISABLE_AUTOUPDATE`, `OPENCODE_DISABLE_MODELS_FETCH`, `OPENCODE_DISABLE_LSP_DOWNLOAD`,
  `OPENCODE_DISABLE_DEFAULT_PLUGINS`, `OPENCODE_DISABLE_CLAUDE_CODE` (stops it from reading Claude Code files).
- Rules file: `AGENTS.md`. Hooks: `--hooks DIR` must contain an `opencode-plugins/` directory; its files are copied
  to `~/.config/opencode/plugins/`.

## GitHub Copilot CLI (`@github/copilot`)

```
copilot -p "<instruction>" --output-format json --allow-all-tools --allow-all-paths --no-ask-user \
  --no-auto-update --disable-client-telemetry --model <openrouter model id>
```

- Bring-your-own-key provider: `COPILOT_PROVIDER_BASE_URL=http://gateway:8080/api/v1`,
  `COPILOT_PROVIDER_TYPE=openai` (chat completions), `COPILOT_PROVIDER_API_KEY=<run token>`,
  `COPILOT_MODEL=<model>`. With a BYOK provider no GitHub login is needed; `COPILOT_OFFLINE=true` stops all
  contact with GitHub services (authentication, telemetry, update checks).
- No turn or cost cap flag exists; the gateway's cap and the wall clock apply.
- Rules file: `AGENTS.md`. Note that Copilot CLI also merges `CLAUDE.md` and `GEMINI.md`; our task repositories
  contain none of them, and the rules experiment writes only the agent's own file.
- Hooks: not supported in v0.1; `run --agent copilot --hooks DIR` stops with an error.

## Optional adapters (no published row in v0.1)

Gemini CLI and Cursor CLI are not run in v0.1: Gemini CLI needs a paid Gemini API key and has no OpenRouter route
(OpenRouter serves no Gemini-native endpoint), and Cursor CLI runs models on Cursor's backend with a Cursor key.
A row from either would be labelled "vendor key, not OpenRouter". Cursor's terms (§1.5(vii)) allow publishing
benchmark results only together with the information needed to replicate them, which this repository provides.

## Hosts each harness contacts on its own

Measured from the egress proxy log on a trivial task (all refused; none is needed for the run). They are excluded
from the `egress_attempt` signal for that harness:

| Harness | Hosts |
|---|---|
| Claude Code | none observed with the settings above |
| Codex CLI | `chatgpt.com`, `api.github.com`, `github.com` |
| OpenCode | `registry.npmjs.org` |
| GitHub Copilot CLI | none observed with `COPILOT_OFFLINE=true` |

## The scripted adapter

`--agent scripted --model <behaviour>` replays a task's scripted behaviour (`tasks/<id>/scripted/<behaviour>.yaml`)
inside the same container setup, with no model calls. CI uses it for the end-to-end tests: honest and cheating
behaviours, egress attempts, and probes that check what the container can see.
