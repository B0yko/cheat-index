"""Starts the model gateway in its own container and talks to its admin API through `docker exec`."""

from __future__ import annotations

import json
import os
import secrets
import time
from typing import Any

from cheat_index import __version__
from cheat_index.runner.containers import Docker, DockerError, tar_from_dir
from cheat_index.runner.package import EXCLUDED, package_dir

IMAGE_TAG = os.environ.get("CHEAT_INDEX_IMAGE_TAG", __version__)
VERIFY_IMAGE = f"cheat-index/verify:{IMAGE_TAG}"

_ADMIN_CLIENT = r"""
import json, os, sys, urllib.request
req = json.load(sys.stdin)
data = json.dumps(req.get("body")).encode() if req.get("body") is not None else None
r = urllib.request.Request("http://127.0.0.1:8080" + req["path"], data=data, method=req["method"],
    headers={"X-Admin-Secret": os.environ["CHEAT_INDEX_ADMIN_SECRET"], "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(r, timeout=120) as resp:
        print(json.dumps({"status": resp.status, "body": json.loads(resp.read() or b"null")}))
except urllib.error.HTTPError as e:
    print(json.dumps({"status": e.code, "body": json.loads(e.read() or b"null")}))
"""


class GatewaySession:
    def __init__(
        self,
        docker: Docker,
        session_id: str,
        *,
        image: str = VERIFY_IMAGE,
        global_cap_usd: float,
        spent_before_usd: float = 0.0,
    ) -> None:
        self.docker = docker
        self.image = image
        self.name = f"ci-gateway-{session_id}"
        self.network = f"ci-egress-{session_id}"
        self.secret = secrets.token_hex(24)
        self.global_cap_usd = global_cap_usd
        self.spent_before_usd = spent_before_usd

    def start(self) -> None:
        self.docker.network_create(self.network, internal=False)
        self.docker.create(
            self.image,
            [
                "python",
                "-m",
                "cheat_index.runner.model_gateway",
                "--host",
                "0.0.0.0",
                "--port",
                "8080",
                "--global-cap-usd",
                f"{self.global_cap_usd:.4f}",
                "--spent-before-usd",
                f"{self.spent_before_usd:.4f}",
            ],
            name=self.name,
            network=self.network,
            env={"CHEAT_INDEX_ADMIN_SECRET": self.secret},
            pass_env=["OPENROUTER_API_KEY"],
            memory="1g",
        )
        self.docker.put_tar(
            self.name, tar_from_dir(package_dir(), "/opt/ci/cheat_index", uid=1001, gid=1001, exclude=EXCLUDED)
        )
        self.docker.start(self.name)
        for _ in range(60):
            try:
                if self.admin("GET", "/admin/status")[0] == 200:
                    return
            except DockerError:
                pass
            time.sleep(0.5)
        raise DockerError("model gateway did not become healthy:\n" + self.docker.logs(self.name).decode()[-2000:])

    def admin(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        payload = json.dumps({"method": method, "path": path, "body": body}).encode()
        proc = self.docker.exec(
            self.name, ["python", "-c", _ADMIN_CLIENT], input=payload, env={"CHEAT_INDEX_ADMIN_SECRET": self.secret}
        )
        if proc.returncode != 0:
            raise DockerError(proc.stderr.decode(errors="replace")[-500:])
        out = json.loads(proc.stdout)
        return int(out["status"]), out["body"]

    def register(self, run_id: str, token: str, models: list[str], max_cost_usd: float, max_tokens: int) -> None:
        status, body = self.admin(
            "POST",
            "/admin/runs",
            {
                "run_id": run_id,
                "token": token,
                "models": models,
                "max_cost_usd": max_cost_usd,
                "max_tokens": max_tokens,
            },
        )
        if status != 201:
            raise DockerError(f"gateway refused run registration: {body}")

    def finish(self, run_id: str) -> dict[str, Any]:
        """Reconcile exact costs, revoke the token and return the run's usage."""
        self.admin("POST", f"/admin/runs/{run_id}/reconcile")
        _, body = self.admin("DELETE", f"/admin/runs/{run_id}")
        return dict(body)

    def key_status(self) -> dict[str, Any]:
        status, body = self.admin("GET", "/admin/key")
        return dict(body) if status == 200 else {}

    def spent_usd(self) -> float:
        _, body = self.admin("GET", "/admin/status")
        return float(body["spent_usd"])

    def connect(self, network: str) -> None:
        self.docker.network_connect(network, self.name, alias="gateway")

    def disconnect(self, network: str) -> None:
        self.docker.network_disconnect(network, self.name)

    def stop(self) -> None:
        self.docker.rm(self.name)
        self.docker.network_rm(self.network)
