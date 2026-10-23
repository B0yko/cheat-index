"""OpenCode: `opencode run --format json`, with its OpenRouter provider pointed at the gateway."""

from __future__ import annotations

import json
from typing import Any

from cheat_index.agents.base import (
    GATEWAY_URL,
    Adapter,
    Event,
    Launch,
    ParsedStream,
    RunConfig,
    as_dict,
    clip,
    json_lines,
)
from cheat_index.tasks.model import Task


class OpenCodeAdapter(Adapter):
    name = "opencode"
    display = "OpenCode"
    package = "opencode-ai"
    binary = "opencode"
    rules_filename = "AGENTS.md"
    harness_hosts: tuple[str, ...] = ("registry.npmjs.org",)  # measured on a no-op task

    def launch(self, task: Task, cfg: RunConfig, token: str) -> Launch:
        env = self.base_env()
        env.update(
            {
                "OPENCODE_DISABLE_AUTOUPDATE": "1",
                "OPENCODE_DISABLE_MODELS_FETCH": "1",
                "OPENCODE_DISABLE_LSP_DOWNLOAD": "1",
                "OPENCODE_DISABLE_DEFAULT_PLUGINS": "1",
                "OPENCODE_DISABLE_CLAUDE_CODE": "1",
            }
        )
        config: dict[str, Any] = {
            "$schema": "https://opencode.ai/config.json",
            "model": f"openrouter/{cfg.model}",
            "share": "disabled",
            "autoupdate": False,
            "snapshot": False,
            "provider": {"openrouter": {"options": {"baseURL": f"{GATEWAY_URL}/api/v1", "apiKey": token}}},
            "permission": {"edit": "allow", "bash": "allow", "webfetch": "allow", "external_directory": "allow"},
            "agent": {"build": {"steps": cfg.max_turns}},
        }
        home_files = {".config/opencode/opencode.json": json.dumps(config, indent=2)}
        if cfg.hooks_dir is not None:
            for p in sorted((cfg.hooks_dir / "opencode-plugins").glob("*")):
                home_files[f".config/opencode/plugins/{p.name}"] = p.read_text(encoding="utf-8")
        flags = ["run", "--format", "json", "-m", f"openrouter/{cfg.model}", "--auto"]
        work_files = {self.rules_filename: rules} if (rules := cfg.rules_text()) else {}
        return Launch(
            argv=[self.binary, *flags, self.prompt(task)],
            env=env,
            home_files=home_files,
            work_files=work_files,
            flags=flags,
        )

    def parse(self, stdout: str, stderr: str) -> ParsedStream:
        events: list[Event] = []
        texts_since_tool: list[str] = []
        cost = 0.0
        tokens: dict[str, int] = {}
        steps = 0
        error: str | None = None
        for obj in json_lines(stdout):
            t = obj.get("type")
            part = as_dict(obj.get("part"))
            if t == "text":
                text = str(part.get("text") or "")
                if text.strip():
                    texts_since_tool.append(text)
                    events.append(Event("message", "agent", content=text))
            elif t == "tool_use":
                state = as_dict(part.get("state"))
                name = str(part.get("tool") or "tool")
                texts_since_tool = []
                events.append(Event("tool_call", "agent", name=name, args=dict(state.get("input") or {})))
                status = state.get("status")
                events.append(
                    Event(
                        "tool_result",
                        "tool",
                        name=name,
                        ok=status == "completed",
                        output={"text": clip(str(state.get("output") or state.get("error") or ""), 3000)},
                    )
                )
            elif t == "step_finish":
                steps += 1
                if isinstance(part.get("cost"), int | float):
                    cost += float(part["cost"])
                for k, v in (part.get("tokens") or {}).items():
                    if isinstance(v, int):
                        tokens[k] = tokens.get(k, 0) + v
            elif t == "error":
                err = obj.get("error")
                error = json.dumps(err)[:2000] if err is not None else "error event"
        final = "\n".join(texts_since_tool).strip()
        return ParsedStream(
            events,
            final,
            num_turns=steps or None,
            reported_cost_usd=cost or None,
            reported_usage=tokens,
            error=error or (None if final else clip(stderr.strip(), 2000) or "no final text"),
            session_ok=bool(final) and error is None,
        )
