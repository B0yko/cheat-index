"""Runs many (task, repeat) pairs for one configuration: concurrency, cost ledger, resume and one retry."""

from __future__ import annotations

import json
import secrets
import shutil
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cheat_index.agents import get_adapter
from cheat_index.agents.base import RunConfig
from cheat_index.runner.containers import Docker
from cheat_index.runner.gateway import GatewaySession
from cheat_index.runner.ledger import Ledger
from cheat_index.runner.run import RunSpec, execute_run
from cheat_index.tasks.model import Task

Progress = Callable[[str], None]


@dataclass
class BatchResult:
    finished: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    not_started: list[str] = field(default_factory=list)
    spent_usd: float = 0.0


def _say(text: str) -> None:
    print(text, flush=True)


def run_dir_for(out: Path, cfg: RunConfig, spec: RunSpec) -> Path:
    return out / cfg.slug() / spec.run_id


def _finished(run_dir: Path) -> dict[str, Any] | None:
    rec = run_dir / "record.json"
    if not rec.is_file():
        return None
    data: dict[str, Any] = json.loads(rec.read_text(encoding="utf-8"))
    return data


def _retryable(record: dict[str, Any]) -> bool:
    if record.get("status") == "completed":
        return False
    return not (record.get("usage") or {}).get("cut_off")


def run_batch(
    cfg: RunConfig,
    tasks: list[Task],
    k: int,
    out: Path,
    ledger: Ledger,
    *,
    concurrency: int = 4,
    hardware: str = "",
    docker: Docker | None = None,
    progress: Progress | None = None,
    score: Callable[[Task, Path], None] | None = None,
) -> BatchResult:
    docker = docker or Docker()
    progress = progress or _say
    adapter = get_adapter(cfg.agent)
    specs = [RunSpec(t, cfg, r) for r in range(1, k + 1) for t in tasks]
    result = BatchResult()
    todo: list[RunSpec] = []
    for spec in specs:
        rec = _finished(run_dir_for(out, cfg, spec))
        if rec is not None and (not _retryable(rec) or int(rec.get("attempt", 1)) >= 2):
            result.skipped.append(spec.run_id)
        else:
            todo.append(spec)
    if not todo:
        progress(f"{cfg.slug()}: nothing to do ({len(result.skipped)} runs already finished)")
        return result
    gateway = GatewaySession(
        docker,
        secrets.token_hex(3),
        global_cap_usd=max(0.0, ledger.stop_at_usd - ledger.spent_usd),
    )
    gateway.start()
    lock = threading.Lock()
    stop = threading.Event()

    def one(spec: RunSpec) -> None:
        run_dir = run_dir_for(out, cfg, spec)
        previous = _finished(run_dir)
        attempt = int(previous.get("attempt", 1)) + 1 if previous else 1
        while True:
            key = f"{cfg.slug()}/{spec.run_id}/a{attempt}"
            if stop.is_set() or not ledger.can_start(key, cfg.max_cost_usd):
                stop.set()
                with lock:
                    result.not_started.append(spec.run_id)
                return
            if run_dir.exists():
                shutil.move(run_dir, run_dir.with_name(f"{run_dir.name}.failed-{attempt - 1}"))
            record = execute_run(spec, adapter, docker, gateway, run_dir, hardware=hardware)
            record["attempt"] = attempt
            (run_dir / "record.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
            usage = record.get("usage") or {}
            ledger.record(key, cfg.slug(), float(usage.get("cost_usd") or 0.0), str(usage.get("cost_source", "none")))
            if score is not None:
                score(spec.task, run_dir)
            progress(
                f"{spec.run_id:48} {record['status']:9} ${float(usage.get('cost_usd') or 0):.4f} "
                f"{record.get('wall_s', 0):>6}s  spent ${ledger.spent_usd:.2f}"
            )
            if record["status"] == "completed" or attempt >= 2 or not _retryable(record):
                with lock:
                    result.finished.append(record)
                return
            attempt += 1

    try:
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
            list(pool.map(one, todo))
    finally:
        gateway.stop()
    result.spent_usd = ledger.spent_usd
    return result
