"""Codex CLI: `codex exec --json`, with an OpenRouter-style provider in a throwaway CODEX_HOME."""

from __future__ import annotations

from typing import Any

from cheat_index.agents.base import (
    GATEWAY_URL,
    HOME,
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

CONFIG = """\
model = "{model}"
model_provider = "openrouter"
approval_policy = "never"
sandbox_mode = "danger-full-access"
check_for_update_on_startup = false

[model_providers.openrouter]
name = "OpenRouter"
base_url = "{base_url}"
env_key = "OPENROUTER_API_KEY"
wire_api = "responses"

[analytics]
enabled = false

[feedback]
enabled = false

[history]
persistence = "none"
"""


class CodexAdapter(Adapter):
    name = "codex"
    display = "Codex CLI"
    package = "@openai/codex"
    binary = "codex"
    rules_filename = "AGENTS.md"
    harness_hosts = ("chatgpt.com", "api.openai.com", "ab.chatgpt.com", "api.github.com", "github.com")

    def launch(self, task: Task, cfg: RunConfig, token: str) -> Launch:
        env = self.base_env()
        env.update({"CODEX_HOME": f"{HOME}/.codex", "OPENROUTER_API_KEY": token, "RUST_LOG": "error"})
        flags = [
            "exec",
            "--json",
            "--skip-git-repo-check",
            "--ephemeral",
            "--dangerously-bypass-approvals-and-sandbox",
            "-m",
            cfg.model,
        ]
        work_files = {self.rules_filename: rules} if (rules := cfg.rules_text()) else {}
        home_files = {".codex/config.toml": CONFIG.format(model=cfg.model, base_url=f"{GATEWAY_URL}/api/v1")}
        if cfg.hooks_dir is not None and (cfg.hooks_dir / "codex-hooks.json").is_file():
            home_files[".codex/hooks.json"] = (cfg.hooks_dir / "codex-hooks.json").read_text(encoding="utf-8")
        return Launch(
            argv=[self.binary, *flags, self.prompt(task)],
            env=env,
            home_files=home_files,
            work_files=work_files,
            flags=flags,
        )

    def parse(self, stdout: str, stderr: str) -> ParsedStream:
        events: list[Event] = []
        last_message = ""
        usage: dict[str, Any] = {}
        turns = 0
        error: str | None = None
        for obj in json_lines(stdout):
            t = obj.get("type")
            item = as_dict(obj.get("item"))
            itype = item.get("type")
            if t == "turn.completed":
                turns += 1
                for k, v in (obj.get("usage") or {}).items():
                    if isinstance(v, int):
                        usage[k] = usage.get(k, 0) + v
            elif t in ("turn.failed", "error"):
                err = as_dict(obj.get("error"))
                error = str(err.get("message") or obj.get("message") or t)
            elif t == "item.started" and itype in ("command_execution", "mcp_tool_call", "web_search"):
                events.append(Event("tool_call", "agent", name=itype, args=_args(item)))
            elif t == "item.completed":
                if itype == "agent_message":
                    last_message = str(item.get("text") or "")
                    events.append(Event("message", "agent", content=last_message))
                elif itype in ("command_execution", "mcp_tool_call", "web_search"):
                    if not events or events[-1].kind != "tool_call" or events[-1].name != itype:
                        events.append(Event("tool_call", "agent", name=itype, args=_args(item)))
                    code = item.get("exit_code")
                    events.append(
                        Event(
                            "tool_result",
                            "tool",
                            name=itype,
                            ok=(code == 0) if code is not None else item.get("status") == "completed",
                            output={"text": clip(str(item.get("aggregated_output") or ""), 3000), "exit_code": code},
                        )
                    )
                elif itype == "file_change":
                    events.append(
                        Event("tool_call", "agent", name="file_change", args={"changes": item.get("changes")})
                    )
                    events.append(
                        Event("tool_result", "tool", name="file_change", ok=item.get("status") == "completed")
                    )
        ok = bool(last_message) and error is None
        return ParsedStream(
            events,
            last_message,
            num_turns=turns or None,
            reported_usage=usage,
            error=error or (None if last_message else clip(stderr.strip(), 2000) or "no agent message"),
            session_ok=ok or bool(last_message),
        )


def _args(item: dict[str, Any]) -> dict[str, Any]:
    if "command" in item:
        return {"command": item.get("command")}
    return {k: v for k, v in item.items() if k in ("server", "tool", "arguments", "query")}
