"""Command-line interface: `cheat-index`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cheat_index import __version__
from cheat_index.tasks.model import FAMILY_NAMES, TaskError, load_suite, select


def _cmd_tasks_list(args: argparse.Namespace) -> int:
    tasks = select(load_suite(), args.tasks)
    for t in tasks:
        print(f"{t.id:40} {t.family} {FAMILY_NAMES[t.family]:20} {t.language:10} {t.pressure:7} {t.title}")
    print(f"{len(tasks)} tasks")
    return 0


def _cmd_tasks_show(args: argparse.Namespace) -> int:
    (task,) = select(load_suite(), args.id)[:1]
    print(f"id:          {task.id}")
    print(f"family:      {task.family} ({FAMILY_NAMES[task.family]})")
    print(f"language:    {task.language}")
    print(f"pressure:    {task.pressure}")
    print(f"tests:       {task.visible_test_command}")
    print(f"honest:      {', '.join(task.honest_outcomes)}")
    for w in task.allowed_workarounds:
        print(f"allowed:     {w.detector} on {', '.join(w.paths) or 'any path'}: {w.note}")
    print(f"hash:        {task.content_hash()[:16]}")
    print("files:       " + ", ".join(task.repo_files()))
    print("\ninstruction:\n" + task.instruction)
    return 0


def _cmd_tasks_validate(args: argparse.Namespace) -> int:
    from cheat_index.tasks.validate import validate_task

    tasks = select(load_suite(), args.tasks)
    failures = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(lambda t: validate_task(t, use_scorer=not args.basic), tasks))
    n_beh = 0
    for tc in results:
        n_beh += len(tc.behaviours)
        status = "ok" if tc.ok else "FAIL"
        if not tc.ok or args.verbose:
            print(f"{status:4} {tc.task_id}")
        for p in tc.problems:
            print(f"     task: {p}")
        for b in tc.behaviours:
            if not b.ok:
                for p in b.problems:
                    print(f"     {b.behaviour}: {p}")
        failures += 0 if tc.ok else 1
    print(f"{len(results) - failures}/{len(results)} tasks valid, {n_beh} scripted behaviours checked")
    return 1 if failures else 0


def _cmd_run(args: argparse.Namespace) -> int:
    from cheat_index.runner.commands import run_command

    return run_command(args)


def _cmd_doctor(args: argparse.Namespace) -> int:
    from cheat_index.runner.commands import doctor_command

    return doctor_command(args)


def _cmd_images_build(args: argparse.Namespace) -> int:
    from cheat_index.runner.commands import images_build_command

    return images_build_command(args)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="cheat-index", description="The Agent Cheat Index.")
    ap.add_argument("--version", action="version", version=f"cheat-index {__version__}")
    sub = ap.add_subparsers(dest="command", required=True)

    tasks = sub.add_parser("tasks", help="list, show and validate the task suite")
    tsub = tasks.add_subparsers(dest="tasks_command", required=True)
    p = tsub.add_parser("list", help="list tasks")
    p.add_argument("--tasks", default="all", help="all | F1 | F3,F4 | ids")
    p.set_defaults(func=_cmd_tasks_list)
    p = tsub.add_parser("show", help="show one task")
    p.add_argument("id")
    p.set_defaults(func=_cmd_tasks_show)
    p = tsub.add_parser("validate", help="run every scripted behaviour through verification and detectors")
    p.add_argument("--tasks", default="all")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--basic", action="store_true", help="check test outcomes only, skip detectors")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=_cmd_tasks_validate)

    p = sub.add_parser("run", help="run an agent configuration on the suite (needs Docker and an OpenRouter key)")
    p.add_argument("--agent", required=True, help="claude-code | codex | opencode | copilot | scripted")
    p.add_argument("--model", required=True, help="OpenRouter model id (for scripted: a behaviour name)")
    p.add_argument("--tasks", default="all", help="all | F1 | F3,F4 | task ids")
    p.add_argument("--k", type=int, default=2, help="runs per task")
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--budget", type=float, default=5.0, help="stop starting runs before this many USD are spent")
    p.add_argument("--max-cost-per-run", type=float, default=0.60, help="gateway cut-off per run, USD")
    p.add_argument("--timeout", type=int, default=900, help="wall-clock limit per run, seconds")
    p.add_argument("--max-turns", type=int, default=60)
    p.add_argument("--rules", type=Path, help="rules file placed where the agent reads project rules")
    p.add_argument("--hooks", type=Path, help="directory with agent hook configuration")
    p.add_argument("--label", help="name for this configuration (e.g. rules, hooks)")
    p.add_argument("--out", type=Path, default=Path("cheat-index-runs"))
    p.add_argument("--hardware", default="", help="hardware description stored with every run")
    p.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    p.set_defaults(func=_cmd_run)

    p = sub.add_parser("doctor", help="check the container runtime, images, CLIs, proxy, key and budget")
    p.add_argument("--out", type=Path, default=Path("cheat-index-runs"))
    p.set_defaults(func=_cmd_doctor)

    images = sub.add_parser("images", help="build the agent and verification images")
    isub = images.add_subparsers(dest="images_command", required=True)
    p = isub.add_parser("build", help="docker build the three images")
    p.set_defaults(func=_cmd_images_build)
    return ap


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rc: int = args.func(args)
    except TaskError as exc:
        print(f"cheat-index: {exc}", file=sys.stderr)
        return 2
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
