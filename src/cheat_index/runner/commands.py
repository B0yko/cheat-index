"""Implementations of `cheat-index run`, `doctor` and `images build`."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from cheat_index import __version__
from cheat_index.agents import ADAPTERS, get_adapter
from cheat_index.agents.base import RunConfig
from cheat_index.costs import estimate_per_run
from cheat_index.paths import images_root
from cheat_index.runner.containers import Docker
from cheat_index.runner.gateway import IMAGE_TAG
from cheat_index.runner.ledger import Ledger
from cheat_index.tasks.model import load_suite, select

KEY_ENV = "OPENROUTER_API_KEY"
IMAGES = {"verify": "verify", "agent-python": "python", "agent-node": "node"}


def _confirm(prompt: str) -> bool:
    if not sys.stdin.isatty():
        return False
    return input(prompt).strip().lower() in ("y", "yes")


def run_command(args: argparse.Namespace) -> int:
    tasks = select(load_suite(), args.tasks)
    cfg = RunConfig(
        agent=args.agent,
        model=args.model,
        label=args.label,
        rules_file=args.rules,
        hooks_dir=args.hooks,
        max_turns=args.max_turns,
        max_cost_usd=args.max_cost_per_run,
        timeout_s=args.timeout,
    )
    get_adapter(cfg.agent)
    n = len(tasks) * args.k
    scripted = cfg.agent == "scripted"
    per_run, basis = (0.0, "scripted replay, no model calls") if scripted else estimate_per_run(cfg.agent, cfg.model)
    print(f"configuration: {cfg.slug()}")
    print(f"runs:          {len(tasks)} tasks x k={args.k} = {n}")
    if per_run is None:
        cap = f"hard cap {n} x ${cfg.max_cost_usd:.2f} per run, budget ${args.budget:.2f}"
        print(f"estimated cost: unknown ({basis}); {cap}")
    else:
        print(f"estimated cost: ${per_run * n:.2f} (${per_run:.3f}/run, {basis}); budget stop ${args.budget:.2f}")
    if not args.yes and not _confirm("start? [y/N] "):
        print("not started (pass --yes to skip this question)")
        return 1
    if scripted:
        os.environ.setdefault(KEY_ENV, "scripted-runs-make-no-model-calls")
    elif not os.environ.get(KEY_ENV):
        print(f"cheat-index: set {KEY_ENV} (it stays in the gateway container; agents never see it)", file=sys.stderr)
        return 2
    docker = Docker()
    if not docker.available():
        print("cheat-index: no container runtime (docker info failed); see `cheat-index doctor`", file=sys.stderr)
        return 2
    missing = [
        f"cheat-index/{i}:{IMAGE_TAG}" for i in IMAGES if not docker.image_exists(f"cheat-index/{i}:{IMAGE_TAG}")
    ]
    if missing:
        print(f"cheat-index: missing images {missing}; run `cheat-index images build`", file=sys.stderr)
        return 2
    from cheat_index.runner.orchestrator import run_batch
    from cheat_index.scoring import score_run_dir

    ledger = Ledger.open(args.out / "ledger.json", args.budget)
    result = run_batch(
        cfg,
        tasks,
        args.k,
        args.out,
        ledger,
        concurrency=args.concurrency,
        hardware=args.hardware,
        docker=docker,
        score=score_run_dir,
    )
    print(
        f"finished {len(result.finished)}, skipped (already done) {len(result.skipped)}, "
        f"not started (budget) {len(result.not_started)}; ledger spent ${result.spent_usd:.2f}"
    )
    print(f"score with: cheat-index score {args.out}")
    return 0 if not result.not_started else 3


def doctor_command(args: argparse.Namespace) -> int:
    ok = True

    def line(status: bool, what: str, detail: str = "") -> None:
        nonlocal ok
        ok &= status
        print(f"[{'ok' if status else '!!'}] {what}{': ' + detail if detail else ''}")

    docker = Docker()
    have_docker = docker.available()
    line(have_docker, "container runtime", docker.binary if have_docker else "docker info failed")
    for name in IMAGES:
        image = f"cheat-index/{name}:{IMAGE_TAG}"
        present = have_docker and docker.image_exists(image)
        line(present, f"image {image}", docker.image_id(image)[:19] if present else "missing: cheat-index images build")
    if have_docker and docker.image_exists(f"cheat-index/agent-python:{IMAGE_TAG}"):
        for adapter_name, cls in sorted(ADAPTERS.items()):
            if adapter_name == "scripted":
                continue
            argv = cls().version_argv()
            proc = docker.run("run", "--rm", "--network", "none", "--entrypoint", argv[0],
                              f"cheat-index/agent-python:{IMAGE_TAG}", *argv[1:], check=False)  # fmt: skip
            text = (proc.stdout or proc.stderr).decode(errors="replace").strip().splitlines()
            line(proc.returncode == 0, f"{cls.display} version", text[0] if text else "no output")
    line(_proxy_selftest(), "egress proxy refuses unlisted hosts")
    has_key = bool(os.environ.get(KEY_ENV))
    line(has_key, f"{KEY_ENV}", "present (not shown)" if has_key else "not set")
    if has_key:
        remaining = _limit_remaining(os.environ[KEY_ENV])
        line(remaining is not None, "OpenRouter key limit", f"limit_remaining ${remaining:.2f}" if remaining is not None
             else "could not read /api/v1/key")  # fmt: skip
    ledger_path = args.out / "ledger.json"
    if ledger_path.is_file():
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
        line(True, "project ledger", f"spent ${data.get('spent_usd', 0):.2f} of ${data.get('stop_at_usd', 0):.2f}")
    else:
        line(True, "project ledger", f"none yet at {ledger_path}")
    return 0 if ok else 1


def _proxy_selftest() -> bool:
    from cheat_index.runner.egress_proxy import EgressProxy, Rule, serve

    async def check() -> bool:
        proxy = EgressProxy([Rule("gateway", 8080)])
        server = await serve(proxy, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"CONNECT example.com:443 HTTP/1.1\r\nHost: example.com:443\r\n\r\n")
        await writer.drain()
        reply = await asyncio.wait_for(reader.read(), timeout=5)
        writer.close()
        server.close()
        return reply.startswith(b"HTTP/1.1 403") and proxy.attempts[0]["host"] == "example.com"

    try:
        return asyncio.run(check())
    except OSError:
        return False


def _limit_remaining(key: str) -> float | None:
    import httpx

    try:
        resp = httpx.get("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"}, timeout=20)
        value = resp.json()["data"].get("limit_remaining")
        return float(value) if value is not None else float("inf")
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None


def images_build_command(args: argparse.Namespace) -> int:
    docker = Docker()
    if shutil.which(docker.binary) is None:
        print("cheat-index: docker not found", file=sys.stderr)
        return 2
    root = images_root()
    for name, sub in IMAGES.items():
        tag = f"cheat-index/{name}:{IMAGE_TAG}"
        print(f"building {tag} (cheat-index {__version__})")
        proc = subprocess.run([docker.binary, "build", "-f", str(root / sub / "Dockerfile"), "-t", tag, str(root)])
        if proc.returncode != 0:
            return proc.returncode
    return 0


def default_out() -> Path:
    return Path("cheat-index-runs")
