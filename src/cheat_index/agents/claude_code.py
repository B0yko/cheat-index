"""Claude Code: `claude -p --output-format stream-json --verbose`, routed through the gateway's Messages endpoint."""

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


class ClaudeCodeAdapter(Adapter):
    name = "claude-code"
    display = "Claude Code"
    package = "@anthropic-ai/claude-code"
    binary = "claude"
    rules_filename = "CLAUDE.md"
    harness_hosts: tuple[str, ...] = ()  # measured on a no-op task

    def launch(self, task: Task, cfg: RunConfig, token: str) -> Launch:
        env = self.base_env()
        env.update(
            {
                "ANTHROPIC_BASE_URL": f"{GATEWAY_URL}/api",
                "ANTHROPIC_AUTH_TOKEN": token,
                "ANTHROPIC_API_KEY": "",
                "ANTHROPIC_MODEL": cfg.model,
                "ANTHROPIC_SMALL_FAST_MODEL": cfg.model,
                "ANTHROPIC_DEFAULT_OPUS_MODEL": cfg.model,
                "ANTHROPIC_DEFAULT_SONNET_MODEL": cfg.model,
                "ANTHROPIC_DEFAULT_HAIKU_MODEL": cfg.model,
                "CLAUDE_CODE_SUBAGENT_MODEL": cfg.model,
                "DISABLE_TELEMETRY": "1",
                "DISABLE_ERROR_REPORTING": "1",
                "DISABLE_AUTOUPDATER": "1",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1",
                "CLAUDE_CODE_DISABLE_TERMINAL_TITLE": "1",
                "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
                "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1",
                "CLAUDE_CODE_ATTRIBUTION_HEADER": "0",
                "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1",
            }
        )
        settings: dict[str, Any] = {"skipWebFetchPreflight": True}
        home_files = {".claude/settings.json": ""}
        if cfg.hooks_dir is not None:
            hooks = json.loads((cfg.hooks_dir / "claude-code.json").read_text(encoding="utf-8"))
            settings.update(hooks)
            for p in sorted(cfg.hooks_dir.rglob("*")):
                if p.is_file() and p.name != "claude-code.json":
                    home_files[f".claude/hooks/{p.relative_to(cfg.hooks_dir).as_posix()}"] = p.read_text(
                        encoding="utf-8"
                    )
        home_files[".claude/settings.json"] = json.dumps(settings, indent=2)
        flags = [
            "-p",
            "--output-format",
            "stream-json",
            "--verbose",
            "--permission-mode",
            "bypassPermissions",
            "--permission-prompts",
            "none",
            "--max-turns",
            str(cfg.max_turns),
            "--model",
            cfg.model,
            "--no-session-persistence",
        ]
        work_files = {self.rules_filename: rules} if (rules := cfg.rules_text()) else {}
        return Launch(
            argv=[self.binary, *flags[:1], self.prompt(task), *flags[1:]],
            env=env,
            home_files=home_files,
            work_files=work_files,
            flags=flags,
        )

    def parse(self, stdout: str, stderr: str) -> ParsedStream:
        events: list[Event] = []
        final = ""
        result: dict[str, Any] | None = None
        last_text = ""
        for obj in json_lines(stdout):
            t = obj.get("type")
            msg = as_dict(obj.get("message"))
            if t == "assistant":
                for block in msg.get("content") or []:
                    if block.get("type") == "text" and block.get("text"):
                        last_text = str(block["text"])
                        events.append(Event("message", "agent", content=last_text))
                    elif block.get("type") == "tool_use":
                        events.append(
                            Event(
                                "tool_call", "agent", name=str(block.get("name")), args=dict(block.get("input") or {})
                            )
                        )
            elif t == "user":
                content = msg.get("content")
                if isinstance(content, str):
                    events.append(Event("message", "user", content=content))
                    continue
                for block in content or []:
                    if block.get("type") == "tool_result":
                        out = block.get("content")
                        text = (
                            out
                            if isinstance(out, str)
                            else "\n".join(str(b.get("text", "")) for b in out or [] if isinstance(b, dict))
                        )
                        name = _tool_name_for(events)
                        events.append(
                            Event(
                                "tool_result",
                                "tool",
                                name=name,
                                ok=not block.get("is_error", False),
                                output={"text": clip(text, 3000)},
                            )
                        )
            elif t == "result":
                result = obj
        if result is not None:
            final = str(result.get("result") or last_text or "")
            ok = not result.get("is_error", False) and result.get("subtype") in ("success", None)
            return ParsedStream(
                events,
                final,
                num_turns=result.get("num_turns"),
                reported_cost_usd=result.get("total_cost_usd"),
                reported_usage=dict(result.get("usage") or {}),
                error=None if ok else str(result.get("subtype") or result.get("result") or "error"),
                session_ok=ok or bool(final),
            )
        return ParsedStream(events, last_text, error=clip(stderr.strip(), 2000) or "no result event", session_ok=False)


def _tool_name_for(events: list[Event]) -> str | None:
    for e in reversed(events):
        if e.kind == "tool_call":
            return e.name
    return None
