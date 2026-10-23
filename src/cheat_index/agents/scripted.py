"""Scripted adapter: replays a task's honest or cheating behaviour in a real container, with no model calls.

The model id names the behaviour file under the task's `scripted/` directory (`honest`, `cheat-edit-test` …).
Used by the end-to-end tests and CI to exercise containers, the proxy, verification and scoring.
"""

from __future__ import annotations

import json
from pathlib import Path

from cheat_index.agents.base import Adapter, Event, Launch, ParsedStream, RunConfig, json_lines
from cheat_index.tasks.behaviour import load_behaviour
from cheat_index.tasks.model import Task

REPLAY = Path(__file__).with_name("scripted_replay.py")


class ScriptedAdapter(Adapter):
    name = "scripted"
    display = "Scripted replay"
    binary = "python3"

    def launch(self, task: Task, cfg: RunConfig, token: str) -> Launch:
        behaviour = load_behaviour(task.scripted_dir / f"{cfg.model}.yaml")
        return Launch(
            argv=["python3", "/home/agent/.scripted/replay.py", "/home/agent/.scripted/behaviour.json"],
            env=self.base_env(),
            home_files={
                ".scripted/replay.py": REPLAY.read_text(encoding="utf-8"),
                ".scripted/behaviour.json": json.dumps(behaviour.to_payload()),
            },
            flags=[f"behaviour={cfg.model}"],
        )

    def version_argv(self) -> list[str]:
        return ["python3", "--version"]

    def parse(self, stdout: str, stderr: str) -> ParsedStream:
        events: list[Event] = []
        final = ""
        for obj in json_lines(stdout):
            t = obj.get("type")
            if t == "message":
                events.append(Event("message", str(obj.get("role", "user")), content=obj.get("content")))
            elif t == "tool_call":
                events.append(Event("tool_call", "agent", name=obj.get("name"), args=dict(obj.get("args") or {})))
            elif t == "tool_result":
                events.append(
                    Event(
                        "tool_result",
                        "tool",
                        name=obj.get("name"),
                        ok=obj.get("ok"),
                        output=dict(obj.get("output") or {}),
                    )
                )
            elif t == "final":
                final = str(obj.get("text", ""))
                events.append(Event("message", "agent", content=final))
        return ParsedStream(events, final, num_turns=1, session_ok=bool(final) or not stderr.strip())
