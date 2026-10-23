"""One run: a fresh agent container on its own internal network, then a network-less verification container.

Directory layout of a finished run (`<out>/<config slug>/<run id>/`):
  record.json    the full run record (also the input for scoring)
  stream.jsonl   the agent's raw machine-readable output
  stderr.txt     the agent's stderr
  changes.json   changed files with before/after text (what detectors read)
  final.diff     unified diff of the end state against the start state
  proxy.jsonl    every egress attempt seen by the proxy
  verify.json    visible-test run, hidden-check run, TypeScript test facts
"""

from __future__ import annotations

import json
import secrets
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cheat_index.agents.base import HOME, WORKDIR, Adapter, RunConfig, clip
from cheat_index.diffing import diff_trees, unified_all
from cheat_index.runner.containers import Docker, DockerError, extract_tar, tar_from_dir, tar_from_files
from cheat_index.runner.gateway import IMAGE_TAG, VERIFY_IMAGE, GatewaySession
from cheat_index.runner.package import EXCLUDED, package_dir
from cheat_index.tasks.model import Task
from cheat_index.verification import VerifyResult

RECORD_SCHEMA = "cheat-index/run/v1"


@dataclass
class RunSpec:
    task: Task
    config: RunConfig
    repeat: int

    @property
    def run_id(self) -> str:
        return f"{self.task.id}--k{self.repeat}"


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def prepare_start_dir(task: Task, work_files: dict[str, str], dest: Path) -> None:
    """The repository exactly as the agent receives it: task repo + rules files, committed to a fresh git repo."""
    shutil.copytree(task.repo_dir, dest)
    for rel, text in work_files.items():
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    env = {
        "GIT_AUTHOR_NAME": "dev",
        "GIT_AUTHOR_EMAIL": "dev@localhost",
        "GIT_COMMITTER_NAME": "dev",
        "GIT_COMMITTER_EMAIL": "dev@localhost",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        "HOME": str(dest),
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
    }
    for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "Initial commit"]):
        subprocess.run(["git", *args], cwd=dest, env=env, check=True, capture_output=True)


def _image_for(adapter: Adapter, task: Task) -> str:
    return adapter.images[task.language]


def execute_run(
    spec: RunSpec,
    adapter: Adapter,
    docker: Docker,
    gateway: GatewaySession,
    out_dir: Path,
    *,
    image_tag: str = IMAGE_TAG,
    verify_image: str = VERIFY_IMAGE,
    hardware: str = "",
) -> dict[str, Any]:
    """Run one agent on one task and write the run directory. Returns the record (unscored)."""
    task, cfg = spec.task, spec.config
    out_dir.mkdir(parents=True, exist_ok=True)
    nonce = secrets.token_hex(4)
    net = f"ci-run-{nonce}"
    proxy_name, agent_name, verify_name = f"ci-proxy-{nonce}", f"ci-agent-{nonce}", f"ci-verify-{nonce}"
    token = "ci-" + secrets.token_urlsafe(24)
    launch = adapter.launch(task, cfg, token)
    image = f"{_image_for(adapter, task)}:{image_tag}"
    record: dict[str, Any] = {
        "schema": RECORD_SCHEMA,
        "run_id": spec.run_id,
        "repeat": spec.repeat,
        "config": {
            "slug": cfg.slug(),
            "agent": adapter.name,
            "agent_display": adapter.display,
            "model": cfg.model,
            "provider": "openrouter",
            "label": cfg.label,
            "flags": launch.flags,
            "rules_sha256": _sha(cfg.rules_text()) if cfg.rules_file else None,
            "hooks": cfg.hooks_dir.name if cfg.hooks_dir else None,
            "image": image,
            "image_id": docker.image_id(image),
            "cli_version": None,
            "max_turns": cfg.max_turns,
            "max_cost_usd": cfg.max_cost_usd,
            "timeout_s": cfg.timeout_s,
            "seed": None,
        },
        "task": {
            "id": task.id,
            "family": task.family,
            "language": task.language,
            "pressure": task.pressure,
            "content_hash": task.content_hash(),
        },
        "hardware": hardware,
        "status": "errored",
        "error": None,
    }
    created: list[str] = []
    gateway_connected = False
    with tempfile.TemporaryDirectory(prefix="ci-run-") as tmp:
        tmpd = Path(tmp)
        start_dir, final_dir = tmpd / "start", tmpd / "final"
        prepare_start_dir(task, launch.work_files, start_dir)
        try:
            record["config"]["cli_version"] = _cli_version(docker, image, adapter)
            docker.network_create(net, internal=True)
            gateway.connect(net)
            gateway_connected = True
            allow = ["gateway:8080", *launch.allow_hosts]
            proxy_cmd = ["python", "-m", "cheat_index.runner.egress_proxy", "--host", "0.0.0.0", "--port", "3128"]
            for a in allow:
                proxy_cmd += ["--allow", a]
            proxy_cmd += ["--log", "/tmp/proxy.jsonl"]
            docker.create(verify_image, proxy_cmd, name=proxy_name, network=net, aliases=["proxy"], memory="256m")
            created.append(proxy_name)
            docker.put_tar(
                proxy_name, tar_from_dir(package_dir(), "/opt/ci/cheat_index", uid=1001, gid=1001, exclude=EXCLUDED)
            )
            docker.start(proxy_name)
            gateway.register(spec.run_id + "-" + nonce, token, [cfg.model], cfg.max_cost_usd, cfg.max_tokens)
            docker.create(
                image,
                launch.argv,
                name=agent_name,
                network=net,
                env={**launch.env},
                user="1000:1000",
                workdir=WORKDIR,
                cpus=cfg.cpus,
                memory=cfg.memory,
                pids=cfg.pids,
            )
            created.append(agent_name)
            docker.put_tar(agent_name, tar_from_dir(start_dir, WORKDIR))
            if launch.home_files:
                docker.put_tar(agent_name, tar_from_files({f"{HOME}/{k}": v for k, v in launch.home_files.items()}))
            record["started_at"] = now_iso()
            attached = docker.start_attached(agent_name, cfg.timeout_s)
            record["ended_at"] = now_iso()
            record["wall_s"] = attached.duration_s
            record["exit_code"] = attached.exit_code
            record["timed_out"] = attached.timed_out
            (out_dir / "stream.jsonl").write_bytes(attached.stdout)
            (out_dir / "stderr.txt").write_bytes(attached.stderr[-200_000:])
            extract_tar(docker.get_tar(agent_name, WORKDIR), final_dir)
            proxy_log = docker.get_tar(proxy_name, "/tmp/proxy.jsonl")
            extract_tar(proxy_log, out_dir, strip=0)
            usage = gateway.finish(spec.run_id + "-" + nonce)
            record["usage"] = {k: v for k, v in usage.items() if k != "log"}
            (out_dir / "gateway.json").write_text(json.dumps(usage, indent=1), encoding="utf-8")
            parsed = adapter.parse(
                attached.stdout.decode("utf-8", "replace"), attached.stderr.decode("utf-8", "replace")
            )
            record["final_message"] = parsed.final_message
            record["agent_reported"] = {
                "num_turns": parsed.num_turns,
                "cost_usd": parsed.reported_cost_usd,
                "usage": parsed.reported_usage,
                "error": clip(parsed.error, 2000),
                "session_ok": parsed.session_ok,
            }
            record["events"] = len(parsed.events)
            changes = diff_trees(start_dir, final_dir)
            (out_dir / "final.diff").write_text(unified_all(changes), encoding="utf-8")
            (out_dir / "changes.json").write_text(json.dumps([c.__dict__ for c in changes], indent=1), encoding="utf-8")
            vr = run_verification(docker, task, start_dir, final_dir, verify_name, verify_image)
            created.append(verify_name)
            (out_dir / "verify.json").write_text(json.dumps(vr.to_dict(), indent=1), encoding="utf-8")
            record["status"] = "timeout" if attached.timed_out else "completed"
            if not parsed.session_ok and not attached.timed_out:
                record["status"] = "errored"
                record["error"] = clip(parsed.error or "agent session failed", 2000)
        except (DockerError, subprocess.SubprocessError, OSError, ValueError, KeyError) as exc:
            record["status"] = "errored"
            record["error"] = f"{type(exc).__name__}: {str(exc)[-1500:]}"
        finally:
            for name in created:
                docker.rm(name)
            if gateway_connected:
                gateway.disconnect(net)
            docker.network_rm(net)
    (out_dir / "record.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


def verify_create_args(name: str, image: str, cmd: list[str]) -> list[str]:
    """`docker create` arguments for a verification container: no network at all, non-root, capped."""
    return [
        "create", "--name", name, "--label", "cheat-index=1", "--network", "none", "--user", "1001:1001",
        "--cpus", "2", "--memory", "2g", "--pids-limit", "512", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", image, *cmd,
    ]  # fmt: skip


def run_verification(
    docker: Docker, task: Task, start_dir: Path, final_dir: Path, name: str, image: str = VERIFY_IMAGE
) -> VerifyResult:
    """Visible tests, hidden checks and test facts inside a container with no network at all."""
    docker.run(*verify_create_args(name, image, [
        "python", "-m", "cheat_index.verification", "--task", f"/v/tasks/{task.id}", "--final", "/v/final",
        "--start", "/v/start", "--out", "/v/verify.json",
    ]))  # fmt: skip
    try:
        docker.put_tar(name, tar_from_dir(package_dir(), "/opt/ci/cheat_index", uid=1001, gid=1001, exclude=EXCLUDED))
        task_files = {
            "task.yaml": (task.root / "task.yaml").read_text(encoding="utf-8"),
            "expected.yaml": (task.root / "expected.yaml").read_text(encoding="utf-8"),
        }
        tdir = f"/v/tasks/{task.id}"
        docker.put_tar(name, tar_from_files({f"{tdir}/{k}": v for k, v in task_files.items()}, uid=1001, gid=1001))
        docker.put_tar(name, tar_from_dir(task.repo_dir, f"{tdir}/repo", uid=1001, gid=1001))
        docker.put_tar(name, tar_from_dir(task.hidden_dir, f"{tdir}/hidden", uid=1001, gid=1001))
        docker.put_tar(name, tar_from_dir(start_dir, "/v/start", uid=1001, gid=1001))
        docker.put_tar(name, tar_from_dir(final_dir, "/v/final", uid=1001, gid=1001))
        attached = docker.start_attached(name, 900)
        if attached.exit_code != 0:
            raise DockerError("verification failed: " + attached.stderr.decode(errors="replace")[-1500:])
        with tempfile.TemporaryDirectory() as tmp:
            extract_tar(docker.get_tar(name, "/v/verify.json"), Path(tmp), strip=0)
            return VerifyResult.from_dict(json.loads((Path(tmp) / "verify.json").read_text(encoding="utf-8")))
    finally:
        docker.rm(name)


_VERSION_CACHE: dict[tuple[str, str], str] = {}


def _cli_version(docker: Docker, image: str, adapter: Adapter) -> str:
    key = (image, adapter.name)
    if key not in _VERSION_CACHE:
        proc = docker.run(
            "run", "--rm", "--network", "none", "--entrypoint", adapter.version_argv()[0], image,
            *adapter.version_argv()[1:], check=False, timeout=120,
        )  # fmt: skip
        text = (proc.stdout or proc.stderr).decode(errors="replace").strip().splitlines()
        _VERSION_CACHE[key] = text[0][:120] if text else "unknown"
    return _VERSION_CACHE[key]


def _sha(text: str | None) -> str | None:
    import hashlib

    return hashlib.sha256(text.encode()).hexdigest() if text is not None else None
