"""Thin wrapper over the `docker` CLI: networks, containers, tar copies in and out, and image digests.

Nothing is bind-mounted: files go in and out of containers as tar streams (`docker cp`), so containers see only
what the runner copies into them.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tarfile
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from cheat_index.diffing import IGNORED_DIRS


class DockerError(RuntimeError):
    """A docker command failed."""


@dataclass
class Attached:
    exit_code: int | None
    stdout: bytes
    stderr: bytes
    timed_out: bool
    duration_s: float


def docker_binary() -> str:
    return os.environ.get("CHEAT_INDEX_DOCKER", "docker")


class Docker:
    def __init__(self, binary: str | None = None) -> None:
        self.binary = binary or docker_binary()

    def available(self) -> bool:
        if shutil.which(self.binary) is None:
            return False
        proc = subprocess.run([self.binary, "info", "--format", "{{.ServerVersion}}"], capture_output=True, check=False)
        return proc.returncode == 0

    def run(
        self,
        *args: str,
        input: bytes | None = None,
        check: bool = True,
        timeout: float | None = 600,
        env: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        proc_env = dict(os.environ)
        if env:
            proc_env.update(env)
        proc = subprocess.run(
            [self.binary, *args], input=input, capture_output=True, check=False, timeout=timeout, env=proc_env
        )
        if check and proc.returncode != 0:
            raise DockerError(f"docker {' '.join(args[:3])} failed: {proc.stderr.decode(errors='replace')[-800:]}")
        return proc

    # ---- networks ----------------------------------------------------------------------------------------
    def network_create(self, name: str, *, internal: bool) -> None:
        args = ["network", "create", "--label", "cheat-index=1"]
        if internal:
            args.append("--internal")
        self.run(*args, name)

    def network_connect(self, network: str, container: str, alias: str | None = None) -> None:
        args = ["network", "connect"]
        if alias:
            args += ["--alias", alias]
        self.run(*args, network, container)

    def network_disconnect(self, network: str, container: str) -> None:
        self.run("network", "disconnect", "--force", network, container, check=False)

    def network_rm(self, name: str) -> None:
        self.run("network", "rm", name, check=False)

    # ---- containers --------------------------------------------------------------------------------------
    def create(
        self,
        image: str,
        cmd: list[str],
        *,
        name: str,
        network: str,
        env: Mapping[str, str] | None = None,
        pass_env: Iterable[str] = (),
        user: str | None = None,
        workdir: str | None = None,
        cpus: float | None = None,
        memory: str | None = None,
        pids: int | None = None,
        aliases: Iterable[str] = (),
        publish: Iterable[str] = (),
        read_only: bool = False,
        cap_drop_all: bool = True,
    ) -> str:
        args = ["create", "--name", name, "--label", "cheat-index=1", "--network", network]
        for alias in aliases:
            args += ["--network-alias", alias]
        for k, v in (env or {}).items():
            args += ["--env", f"{k}={v}"]
        for k in pass_env:
            args += ["--env", k]  # value comes from this process's environment, never from the command line
        if user:
            args += ["--user", user]
        if workdir:
            args += ["--workdir", workdir]
        if cpus:
            args += ["--cpus", str(cpus)]
        if memory:
            args += ["--memory", memory, "--memory-swap", memory]
        if pids:
            args += ["--pids-limit", str(pids)]
        for p in publish:
            args += ["--publish", p]
        if read_only:
            args.append("--read-only")
        if cap_drop_all:
            args += ["--cap-drop", "ALL", "--security-opt", "no-new-privileges"]
        args += [image, *cmd]
        return self.run(*args).stdout.decode().strip()

    def start(self, container: str) -> None:
        self.run("start", container)

    def start_attached(self, container: str, timeout_s: float) -> Attached:
        """Start a container, stream its output to memory, and kill it at the wall-clock limit."""
        start = time.monotonic()
        proc = subprocess.Popen(
            [self.binary, "start", "--attach", container], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            out, err = proc.communicate(timeout=timeout_s)
            timed_out = False
        except subprocess.TimeoutExpired:
            self.run("kill", container, check=False)
            out, err = proc.communicate(timeout=60)
            timed_out = True
        code = self.exit_code(container)
        return Attached(code, out, err, timed_out, round(time.monotonic() - start, 2))

    def exit_code(self, container: str) -> int | None:
        proc = self.run("inspect", "--format", "{{.State.ExitCode}}", container, check=False)
        text = proc.stdout.decode().strip()
        return int(text) if text.lstrip("-").isdigit() else None

    def exec(
        self, container: str, cmd: list[str], *, input: bytes | None = None, env: Mapping[str, str] | None = None
    ) -> subprocess.CompletedProcess[bytes]:
        args = ["exec", "-i"]
        for k, v in (env or {}).items():
            args += ["--env", f"{k}={v}"]
        return self.run(*args, container, *cmd, input=input, check=False)

    def logs(self, container: str) -> bytes:
        proc = self.run("logs", container, check=False)
        return proc.stdout + proc.stderr

    def stop(self, container: str) -> None:
        self.run("stop", "--time", "2", container, check=False)

    def rm(self, container: str) -> None:
        self.run("rm", "--force", "--volumes", container, check=False)

    def inspect(self, obj: str) -> dict[str, object]:
        data = json.loads(self.run("inspect", obj).stdout)
        return dict(data[0])

    # ---- files -------------------------------------------------------------------------------------------
    def put_tar(self, container: str, tar_bytes: bytes, dest: str = "/") -> None:
        self.run("cp", "--archive", "-", f"{container}:{dest}", input=tar_bytes)

    def get_tar(self, container: str, src: str) -> bytes:
        return self.run("cp", f"{container}:{src}", "-", timeout=300).stdout

    # ---- images ------------------------------------------------------------------------------------------
    def image_id(self, image: str) -> str:
        return self.run("image", "inspect", "--format", "{{.Id}}", image).stdout.decode().strip()

    def image_exists(self, image: str) -> bool:
        return self.run("image", "inspect", image, check=False).returncode == 0


def tar_from_files(files: Mapping[str, bytes | str], *, uid: int = 1000, gid: int = 1000, mode: int = 0o644) -> bytes:
    """A tar archive holding the given absolute container paths, with parent directories, owned by uid:gid."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        seen: set[str] = set()
        for path in sorted(files):
            p = PurePosixPath(path)
            for parent in reversed(p.parents):
                d = parent.as_posix().lstrip("/")
                if d and d not in seen:
                    seen.add(d)
                    info = tarfile.TarInfo(d)
                    info.type, info.mode, info.uid, info.gid = tarfile.DIRTYPE, 0o755, uid, gid
                    info.mtime = int(time.time())
                    tar.addfile(info)
            raw = files[path]
            data = raw.encode() if isinstance(raw, str) else raw
            info = tarfile.TarInfo(p.as_posix().lstrip("/"))
            info.size, info.mode, info.uid, info.gid = len(data), mode, uid, gid
            info.mtime = int(time.time())
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def tar_from_dir(root: Path, dest: str, *, uid: int = 1000, gid: int = 1000, exclude: Iterable[str] = ()) -> bytes:
    """A tar archive of a host directory placed at an absolute container path, owned by uid:gid.

    `exclude` lists paths relative to `root` (files or directories) to leave out.
    """
    buf = io.BytesIO()
    prefix = dest.lstrip("/")
    skip = {f"{prefix}/{e.strip('/')}" for e in exclude}

    def own(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
        if any(part in IGNORED_DIRS - {".git"} for part in PurePosixPath(info.name).parts):
            return None
        if any(info.name == s or info.name.startswith(s + "/") for s in skip):
            return None
        info.uid, info.gid, info.uname, info.gname = uid, gid, "", ""
        return info

    with tarfile.open(fileobj=buf, mode="w") as tar:
        tar.add(root, arcname=dest.lstrip("/"), filter=own)
    return buf.getvalue()


def extract_tar(tar_bytes: bytes, dest: Path, *, strip: int = 1) -> None:
    """Extract a `docker cp` archive safely (no links, devices or escaping paths), dropping leading components."""
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r") as tar:
        for member in tar.getmembers():
            parts = PurePosixPath(member.name).parts[strip:]
            if (
                not parts
                or ".." in parts
                or member.issym()
                or member.islnk()
                or not (member.isfile() or member.isdir())
            ):
                continue
            target = dest.joinpath(*parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            src = tar.extractfile(member)
            if src is not None:
                target.write_bytes(src.read())
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
