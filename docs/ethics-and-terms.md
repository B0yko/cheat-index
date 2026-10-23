# Ethics and terms

This page records, for every vendor whose software or models produce a published row, what its terms say about
automated use, API-key access, publishing benchmark results and publishing outputs. Terms were read on 2026-10-23;
quotes are short excerpts with links to the full text. If a term had forbidden a row, the row would have been
dropped. None did.

## What this project does and does not do

- It runs agent CLIs with API keys through OpenRouter, never through anyone's subscription login.
- It publishes what agents did (diffs, final messages, hidden-check results) on tasks written for this benchmark,
  and describes behaviour operationally. It makes no claims about intent, and it does not use words such as
  "lying" or "deceptive".
- It publishes everything needed to reproduce or dispute a number: the harness, the tasks, the exact agent
  versions and flags (`docs/agents.md`), per-run summaries in git and raw runs as a release asset.
- It does not redistribute the agent CLIs: the container images are built locally (or in CI) from the pinned npm
  packages and are not published.

## Anthropic (Claude Code; Claude models through OpenRouter)

- Automated access: the consumer terms prohibit accessing the services "through automated or non-human means",
  except "via an Anthropic API Key or where we otherwise explicitly permit it"
  ([Consumer Terms](https://www.anthropic.com/legal/consumer-terms)). We never use a Claude subscription login;
  Claude models are reached with an API key through OpenRouter.
- Claude Code: developers and the Agent SDK "should use API key authentication"
  ([Claude Code legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)). That page also
  says running Claude Code in your own hosted sandboxes falls under the Commercial Terms and requires an unmodified
  binary; we install the unmodified npm package.
- Publishing results and outputs: neither the [Commercial Terms](https://www.anthropic.com/legal/commercial-terms)
  nor the [Usage Policy](https://www.anthropic.com/legal/aup) contains a clause about benchmark results; under the
  Commercial Terms the customer owns outputs.

## OpenAI (Codex CLI)

- API keys for automation: "API keys are still the recommended default for automation."
  ([Codex authentication](https://learn.chatgpt.com/docs/auth)). We use no ChatGPT login; Codex talks to OpenRouter
  through a custom provider.
- Codex CLI is Apache-2.0 ([repository](https://github.com/openai/codex)). OpenAI models are not used in the
  published v0.1 rows, so OpenAI's model terms do not apply to them.

## OpenRouter

- The [Terms of Service](https://openrouter.ai/terms) contain no clause on benchmarks. They point to each model's
  own terms: "You are solely responsible for reviewing the Model Terms applicable to each Model." (5.1), and
  output ownership is "set forth in the Model Terms" (6.1). The model rows below cover those.

## GitHub (Copilot CLI)

- With a bring-your-own-key provider, Copilot CLI needs no GitHub login
  ([changelog, 2026-04-07](https://github.blog/changelog/2026-04-07-copilot-cli-now-supports-byok-and-local-models/));
  we also set `COPILOT_OFFLINE=true`, so it contacts no GitHub service.
- The [Copilot CLI licence](https://github.com/github/copilot-cli/blob/main/LICENSE.md) allows installing and
  running the CLI and limits redistribution; we do not redistribute it.
- The GitHub [Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) say
  "GitHub does not claim ownership of your Input or Output." (J.2). The only benchmarking clause we found
  ([additional product terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features),
  "Competitive Benchmarking") applies to people who offer a competing product, which this project does not.

## OpenCode

- MIT licence ([repository](https://github.com/anomalyco/opencode)); no usage terms beyond the licence.

## Models used in published rows

| Model family | Licence or terms | Publishing outputs and benchmarks |
|---|---|---|
| Anthropic Claude (hosted) | [Commercial Terms](https://www.anthropic.com/legal/commercial-terms) via OpenRouter | no benchmark clause; customer owns outputs |
| Qwen3 Coder | Apache-2.0 ([model card](https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct)) | no restriction in the licence |
| DeepSeek V4 | MIT ([licence](https://huggingface.co/deepseek-ai)); [Open Platform Terms](https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html) | no benchmark clause; output rights assigned to the user |
| Z.ai GLM | MIT; [terms of use](https://docs.z.ai/legal-agreement/terms-of-use) | no benchmark clause |

The exact model ids and the providers OpenRouter routed each request to are recorded per run.

## Optional adapters

- Cursor CLI: the [Terms of Service](https://cursor.com/terms-of-service) (§1.5(vii)) forbid giving third
  parties "the results of any benchmark tests of the Service," "unless you include all necessary information for
  others to replicate the tests". This repository is that information; a Cursor row would also need a Cursor API key
  and is not part of v0.1.
- Gemini CLI: Gemini CLI "remains accessible through paid Gemini" API keys after unpaid users moved to Antigravity
  CLI on 2026-06-18 ([announcement](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/)).
  A Gemini row needs a paid Gemini key and is not part of v0.1.

## Tasks and data

All 40 tasks were written for this repository and are Apache-2.0. They contain no third-party code and no personal
data. Every run's raw output is our own run of a vendor's software on those tasks.
