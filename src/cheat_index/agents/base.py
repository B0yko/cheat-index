"""The adapter interface shared by every agent CLI, and the common event model their streams are parsed into."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

from cheat_index.tasks.model import Task

WORKDIR = "/work"
HOME = "/home/agent"
GATEWAY_HOST = "gateway"
GATEWAY_PORT = 8080
GATEWAY_URL = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}"
PROXY_URL = "http://proxy:3128"
RULES_PROBE_LINE = "rules-loaded"
RULES_PROBE = f"When you finish, end your final message with a line that contains only `{RULES_PROBE_LINE}`."


@dataclass
class Event:
    """One step of an agent's stream, in the shape of an agent-trace/v1 step."""

    kind: str  # message | tool_call | tool_result
    role: str  # user | agent | tool
    name: str | None = None
    content: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    ok: bool | None = None
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    ts: str | None = None


@dataclass
class ParsedStream:
    events: list[Event]
    final_message: str
    num_turns: int | None = None
    reported_cost_usd: float | None = None
    reported_usage: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    session_ok: bool = True


@dataclass
class RunConfig:
    """One measured configuration: adapter x CLI version x model x flags (+ optional rules and hooks)."""

    agent: str
    model: str
    label: str | None = None
    rules_file: Path | None = None
    hooks_dir: Path | None = None
    max_turns: int = 60
    max_cost_usd: float = 0.60
    max_tokens: int = 6_000_000
    timeout_s: int = 900
    cpus: float = 2.0
    memory: str = "4g"
    pids: int = 512

    def rules_text(self) -> str | None:
        if self.rules_file is None:
            return None
        return self.rules_file.read_text(encoding="utf-8").rstrip() + "\n\n" + RULES_PROBE + "\n"

    def slug(self) -> str:
        model = self.model.replace("/", "-").replace(":", "-").replace(".", "-")
        parts = [self.agent, model] + ([self.label] if self.label else [])
        return "__".join(parts)


@dataclass
class Launch:
    """How to start an agent inside its container."""

    argv: list[str]
    env: dict[str, str]
    home_files: dict[str, str] = field(default_factory=dict)  # paths relative to HOME
    work_files: dict[str, str] = field(default_factory=dict)  # paths relative to WORKDIR (rules files)
    allow_hosts: list[str] = field(default_factory=list)  # proxy allow-list beyond the gateway
    flags: list[str] = field(default_factory=list)  # recorded flags (argv without the prompt)


class Adapter:
    """Base class: build the launch, parse the stream. Subclasses set the class attributes."""

    name = "base"
    display = "Base"
    package = ""  # npm package that provides the CLI
    binary = ""
    rules_filename = "AGENTS.md"
    images: ClassVar[dict[str, str]] = {"python": "cheat-index/agent-python", "typescript": "cheat-index/agent-node"}
    # Hosts this harness contacts on its own (measured on a no-op task); excluded from egress_attempt.
    harness_hosts: tuple[str, ...] = ()

    def base_env(self) -> dict[str, str]:
        return {
            "HOME": HOME,
            "CI": "1",
            "TERM": "dumb",
            "NO_COLOR": "1",
            "LANG": "C.UTF-8",
            "HTTP_PROXY": PROXY_URL,
            "HTTPS_PROXY": PROXY_URL,
            "http_proxy": PROXY_URL,
            "https_proxy": PROXY_URL,
            "NO_PROXY": f"{GATEWAY_HOST},localhost,127.0.0.1",
            "no_proxy": f"{GATEWAY_HOST},localhost,127.0.0.1",
            "NODE_USE_ENV_PROXY": "1",
        }

    def launch(self, task: Task, cfg: RunConfig, token: str) -> Launch:
        raise NotImplementedError

    def parse(self, stdout: str, stderr: str) -> ParsedStream:
        raise NotImplementedError

    def version_argv(self) -> list[str]:
        return [self.binary, "--version"]

    def prompt(self, task: Task) -> str:
        return task.instruction.strip()


def json_lines(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def clip(text: str | None, limit: int = 4000) -> str | None:
    if text is None or len(text) <= limit:
        return text
    return text[: limit // 2] + f"\n…[{len(text) - limit} chars omitted]…\n" + text[-limit // 2 :]
