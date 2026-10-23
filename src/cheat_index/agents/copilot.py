"""GitHub Copilot CLI: `copilot -p --output-format json`, bring-your-own-key provider pointed at the gateway."""

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


class CopilotAdapter(Adapter):
    name = "copilot"
    display = "GitHub Copilot CLI"
    package = "@github/copilot"
    binary = "copilot"
    rules_filename = "AGENTS.md"
    harness_hosts = ("api.github.com", "github.com", "api.githubcopilot.com", "copilot-telemetry.githubusercontent.com")

    def launch(self, task: Task, cfg: RunConfig, token: str) -> Launch:
        env = self.base_env()
        env.update(
            {
                "COPILOT_HOME": f"{HOME}/.copilot",
                "COPILOT_PROVIDER_BASE_URL": f"{GATEWAY_URL}/api/v1",
                "COPILOT_PROVIDER_TYPE": "openai",
                "COPILOT_PROVIDER_API_KEY": token,
                "COPILOT_MODEL": cfg.model,
                "COPILOT_OFFLINE": "true",
                "COPILOT_AUTO_UPDATE": "false",
            }
        )
        flags = [
            "-p",
            "--output-format",
            "json",
            "--allow-all-tools",
            "--allow-all-paths",
            "--no-ask-user",
            "--no-auto-update",
            "--disable-client-telemetry",
            "--model",
            cfg.model,
        ]
        if cfg.hooks_dir is not None:
            env["GITHUB_COPILOT_PROMPT_MODE_REPO_HOOKS"] = "true"
        work_files = {self.rules_filename: rules} if (rules := cfg.rules_text()) else {}
        return Launch(
            argv=[self.binary, flags[0], self.prompt(task), *flags[1:]],
            env=env,
            work_files=work_files,
            flags=flags,
        )

    def parse(self, stdout: str, stderr: str) -> ParsedStream:
        events: list[Event] = []
        last_message = ""
        error: str | None = None
        usage: dict[str, Any] = {}
        turns = 0
        names: dict[str, str] = {}
        for obj in json_lines(stdout):
            t = str(obj.get("type") or "")
            data = as_dict(obj.get("data")) or obj
            if t == "assistant.message":
                content = data.get("content")
                text = content if isinstance(content, str) else ""
                if text.strip():
                    last_message = text
                    events.append(Event("message", "agent", content=text))
            elif t == "tool.execution_start":
                name = str(data.get("toolName") or "tool")
                names[str(data.get("toolCallId"))] = name
                events.append(Event("tool_call", "agent", name=name, args=as_dict(data.get("arguments"))))
            elif t == "tool.execution_complete":
                result = data.get("result")
                output = as_dict(result).get("content") if isinstance(result, dict) else result
                shell = as_dict(data.get("shellExecution"))
                events.append(
                    Event(
                        "tool_result",
                        "tool",
                        name=names.get(str(data.get("toolCallId")), str(data.get("toolName") or "tool")),
                        ok=bool(data.get("success", True)),
                        output={"text": clip(str(output or ""), 3000), "exit_code": shell.get("exitCode")},
                    )
                )
            elif t == "assistant.turn_end":
                turns += 1
            elif t == "result" and obj.get("exitCode") not in (0, None):
                error = f"exit code {obj.get('exitCode')}"
            elif t in ("session.error", "error"):
                error = str(data.get("message") or data)[:2000]
        return ParsedStream(
            events,
            last_message,
            num_turns=turns or None,
            reported_usage=usage,
            error=error or (None if last_message else clip(stderr.strip(), 2000) or "no assistant message"),
            session_ok=bool(last_message) and error is None,
        )
