"""Agent adapters, by name."""

from __future__ import annotations

from cheat_index.agents.base import Adapter
from cheat_index.agents.claude_code import ClaudeCodeAdapter
from cheat_index.agents.codex import CodexAdapter
from cheat_index.agents.copilot import CopilotAdapter
from cheat_index.agents.opencode import OpenCodeAdapter
from cheat_index.agents.scripted import ScriptedAdapter

ADAPTERS: dict[str, type[Adapter]] = {
    a.name: a for a in (ClaudeCodeAdapter, CodexAdapter, OpenCodeAdapter, CopilotAdapter, ScriptedAdapter)
}


def get_adapter(name: str) -> Adapter:
    try:
        return ADAPTERS[name]()
    except KeyError:
        raise ValueError(f"unknown agent {name!r}; choose from {', '.join(sorted(ADAPTERS))}") from None
