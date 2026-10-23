"""Replays a scripted behaviour inside an agent container (standard library only).

Usage: python3 scripted_replay.py BEHAVIOUR.json  (run with the task repository as the working directory)
Prints JSON Lines events in the same spirit as real agent streams.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def emit(**event: object) -> None:
    sys.stdout.write(json.dumps(event) + "\n")
    sys.stdout.flush()


def main(path: str) -> int:
    b = json.loads(Path(path).read_text(encoding="utf-8"))
    root = Path.cwd()
    emit(type="message", role="user", content="(scripted behaviour " + b["name"] + ")")
    for src, dst in b.get("rename", []):
        emit(type="tool_call", name="rename", args={"from": src, "to": dst})
        (root / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root / src), str(root / dst))
        emit(type="tool_result", name="rename", ok=True)
    for rel in b.get("delete", []):
        emit(type="tool_call", name="delete", args={"path": rel})
        target = root / rel
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        emit(type="tool_result", name="delete", ok=True)
    for e in b.get("edits", []):
        emit(type="tool_call", name="edit", args={"path": e["path"]})
        p = root / e["path"]
        text = p.read_text(encoding="utf-8")
        ok = text.count(e["old"]) == 1
        if ok:
            p.write_text(text.replace(e["old"], e["new"]), encoding="utf-8")
        emit(type="tool_result", name="edit", ok=ok)
    for rel, content in b.get("write", {}).items():
        emit(type="tool_call", name="write", args={"path": rel})
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        emit(type="tool_result", name="write", ok=True)
    for cmd in b.get("commands", []):
        emit(type="tool_call", name="bash", args={"command": cmd})
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        emit(
            type="tool_result",
            name="bash",
            ok=proc.returncode == 0,
            output={"exit_code": proc.returncode, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]},
        )
    emit(type="final", text=b.get("final_message", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
