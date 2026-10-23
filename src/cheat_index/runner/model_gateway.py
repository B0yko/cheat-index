"""Key-holding model gateway between agent containers and OpenRouter.

Agents get a per-run dummy token and a plain-HTTP base URL pointing here. The gateway maps the token to its run,
swaps in the real key, forwards the request (streaming responses pass through unchanged), reads token usage and
cost from the response, and refuses further requests once a run exceeds its token or cost cap, or the global
budget is spent. The real key never leaves this process.

Admin API (for the orchestrator only; requires the `X-Admin-Secret` header, a loopback or `gateway` Host header and
no `Origin` header):
  POST   /admin/runs                {run_id, token, models, max_cost_usd, max_tokens}
  GET    /admin/runs/<run_id>       usage, requests and cut-off state
  DELETE /admin/runs/<run_id>       revoke the token
  POST   /admin/runs/<run_id>/reconcile   look up exact costs with GET /api/v1/generation?id=
  GET    /admin/key                 the key's limit and limit_remaining (never the key)
  GET    /admin/status              totals
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import secrets
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import httpx

UPSTREAM = "https://openrouter.ai/api"
MAX_HEAD = 64 * 1024
MAX_BODY = 32 * 1024 * 1024
HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "content-encoding",
    "host",
}
ADMIN_HOSTS = {"127.0.0.1", "localhost", "gateway", "[::1]"}


@dataclass
class Price:
    prompt: float  # USD per token
    completion: float


@dataclass
class RequestRecord:
    ts: float
    path: str
    model: str | None
    status: int
    duration_s: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    cost_reported: float | None = None
    cost_estimated: float = 0.0
    cost_reconciled: float | None = None
    generation_id: str | None = None
    provider: str | None = None
    refused: str | None = None

    @property
    def cost(self) -> float:
        if self.cost_reconciled is not None:
            return self.cost_reconciled
        if self.cost_reported is not None:
            return self.cost_reported
        return self.cost_estimated


@dataclass
class RunState:
    run_id: str
    token: str
    models: list[str]
    max_cost_usd: float
    max_tokens: int
    requests: list[RequestRecord] = field(default_factory=list)
    cut_off: str | None = None
    revoked: bool = False

    @property
    def cost_usd(self) -> float:
        return sum(r.cost for r in self.requests)

    @property
    def tokens(self) -> int:
        return sum(r.prompt_tokens + r.completion_tokens for r in self.requests)

    def summary(self) -> dict[str, Any]:
        reported = all(
            r.cost_reported is not None or r.cost_reconciled is not None for r in self.requests if r.status == 200
        )
        return {
            "run_id": self.run_id,
            "models": self.models,
            "requests": len(self.requests),
            "prompt_tokens": sum(r.prompt_tokens for r in self.requests),
            "completion_tokens": sum(r.completion_tokens for r in self.requests),
            "cached_tokens": sum(r.cached_tokens for r in self.requests),
            "cost_usd": round(self.cost_usd, 6),
            "cost_source": "provider" if reported else "estimate",
            "cut_off": self.cut_off,
            "refused_requests": sum(1 for r in self.requests if r.refused),
            "providers": sorted({r.provider for r in self.requests if r.provider}),
            "log": [asdict(r) for r in self.requests],
        }


class UsageParser:
    """Collects usage, cost, model and generation id from a JSON body or an SSE stream, incrementally."""

    def __init__(self, streaming: bool) -> None:
        self.streaming = streaming
        self.buf = b""
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cached_tokens = 0
        self.cost: float | None = None
        self.model: str | None = None
        self.generation_id: str | None = None

    def feed(self, chunk: bytes) -> None:
        self.buf += chunk
        if not self.streaming:
            return
        while b"\n" in self.buf:
            line, self.buf = self.buf.split(b"\n", 1)
            self._sse_line(line.strip())

    def close(self) -> None:
        if self.streaming:
            self._sse_line(self.buf.strip())
        else:
            with contextlib.suppress(ValueError):
                self._event(json.loads(self.buf.decode("utf-8", "replace") or "null"))
        self.buf = b""

    def _sse_line(self, line: bytes) -> None:
        if not line.startswith(b"data:"):
            return
        payload = line[5:].strip()
        if not payload or payload == b"[DONE]":
            return
        with contextlib.suppress(ValueError):
            self._event(json.loads(payload))

    def _event(self, obj: Any) -> None:
        if not isinstance(obj, dict):
            return
        # Anthropic messages stream: message_start carries message.usage; message_delta carries usage.
        # Responses API stream: response.completed carries response.usage.
        for container in (obj, obj.get("message"), obj.get("response")):
            if not isinstance(container, dict):
                continue
            gid = container.get("id")
            if isinstance(gid, str) and gid and self.generation_id is None:
                self.generation_id = gid
            model = container.get("model")
            if isinstance(model, str) and model:
                self.model = model
            usage = container.get("usage")
            if isinstance(usage, dict):
                self._usage(usage)

    def _usage(self, u: dict[str, Any]) -> None:
        def num(*keys: str) -> int | None:
            for k in keys:
                v = u.get(k)
                if isinstance(v, int | float):
                    return int(v)
            return None

        p = num("prompt_tokens", "input_tokens")
        c = num("completion_tokens", "output_tokens")
        if p is not None:
            cache_read = num("cache_read_input_tokens") or 0
            cache_write = num("cache_creation_input_tokens") or 0
            # Anthropic-style usage reports cached input separately from input_tokens.
            self.prompt_tokens = max(self.prompt_tokens, p + (cache_read + cache_write if "input_tokens" in u else 0))
        if c is not None:
            self.completion_tokens = max(self.completion_tokens, c)
        details = u.get("prompt_tokens_details") or u.get("input_tokens_details") or {}
        if isinstance(details, dict) and isinstance(details.get("cached_tokens"), int):
            self.cached_tokens = max(self.cached_tokens, int(details["cached_tokens"]))
        if isinstance(u.get("cache_read_input_tokens"), int):
            self.cached_tokens = max(self.cached_tokens, int(u["cache_read_input_tokens"]))
        cost = u.get("cost")
        if isinstance(cost, int | float):
            self.cost = float(cost)


class Gateway:
    def __init__(
        self,
        api_key: str,
        admin_secret: str,
        *,
        upstream: str = UPSTREAM,
        prices: dict[str, Price] | None = None,
        global_cap_usd: float = float("inf"),
        spent_before_usd: float = 0.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self.admin_secret = admin_secret
        self.upstream = upstream.rstrip("/")
        self.prices = prices or {}
        self.global_cap_usd = global_cap_usd
        self.spent_before_usd = spent_before_usd
        self.runs: dict[str, RunState] = {}
        self.by_token: dict[str, RunState] = {}
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(900.0, connect=30.0), transport=transport, follow_redirects=False
        )

    @property
    def spent_usd(self) -> float:
        return self.spent_before_usd + sum(r.cost_usd for r in self.runs.values())

    # ---- HTTP plumbing -------------------------------------------------------------------------------------
    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while True:
                req = await _read_request(reader)
                if req is None:
                    break
                method, path, headers, body = req
                keep = await self.dispatch(method, path, headers, body, writer)
                if not keep or headers.get("connection", "").lower() == "close":
                    break
        except (ConnectionError, asyncio.IncompleteReadError, ValueError):
            pass
        finally:
            with contextlib.suppress(Exception):
                writer.close()

    async def dispatch(
        self, method: str, path: str, headers: dict[str, str], body: bytes, writer: asyncio.StreamWriter
    ) -> bool:
        if path.startswith("/admin/") or path == "/admin":
            status, payload = await self.admin(method, path, headers, body)
            await _send_json(writer, status, payload)
            return True
        if path == "/health":
            await _send_json(writer, 200, {"ok": True})
            return True
        if not path.startswith("/api/"):
            await _send_json(writer, 404, _error("unknown path"))
            return True
        return await self.proxy(method, path, headers, body, writer)

    # ---- model traffic --------------------------------------------------------------------------------------
    def _run_for(self, headers: dict[str, str]) -> RunState | None:
        token = headers.get("x-api-key") or ""
        auth = headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
        run = self.by_token.get(token)
        if run is None or run.revoked:
            return None
        return run

    def _refuse_reason(self, run: RunState, model: str | None) -> str | None:
        if run.cut_off:
            return run.cut_off
        if run.cost_usd >= run.max_cost_usd:
            run.cut_off = f"run cost cap ${run.max_cost_usd:.2f} reached"
            return run.cut_off
        if run.tokens >= run.max_tokens:
            run.cut_off = f"run token cap {run.max_tokens} reached"
            return run.cut_off
        if self.spent_usd >= self.global_cap_usd:
            run.cut_off = f"global budget ${self.global_cap_usd:.2f} reached"
            return run.cut_off
        if model is not None and run.models and model not in run.models:
            return f"model {model!r} is not configured for this run"
        return None

    def _estimate(self, model: str | None, prompt: int, completion: int, cached: int) -> float:
        price = self.prices.get(model or "")
        if price is None:
            return 0.0
        return prompt * price.prompt + completion * price.completion

    async def proxy(
        self, method: str, path: str, headers: dict[str, str], body: bytes, writer: asyncio.StreamWriter
    ) -> bool:
        run = self._run_for(headers)
        if run is None:
            await _send_json(writer, 401, _error("unknown or revoked token"))
            return True
        model: str | None = None
        if body and method == "POST":
            with contextlib.suppress(ValueError):
                parsed = json.loads(body)
                if isinstance(parsed, dict) and isinstance(parsed.get("model"), str):
                    model = parsed["model"]
        start = time.time()
        reason = self._refuse_reason(run, model)
        if reason:
            run.requests.append(RequestRecord(start, path, model, 402, 0.0, refused=reason))
            await _send_json(writer, 402, _error(f"cheat-index gateway: {reason}"))
            return True
        up_headers = {k: v for k, v in headers.items() if k not in HOP_BY_HOP | {"authorization", "x-api-key"}}
        up_headers["authorization"] = f"Bearer {self._api_key}"
        up_headers["accept-encoding"] = "identity"
        up_headers.setdefault("x-title", "cheat-index")
        url = self.upstream + path[len("/api") :]
        rec = RequestRecord(start, path, model, 0, 0.0)
        run.requests.append(rec)
        try:
            async with self.client.stream(method, url, headers=up_headers, content=body) as resp:
                rec.status = resp.status_code
                ctype = resp.headers.get("content-type", "")
                parser = UsageParser(streaming="text/event-stream" in ctype)
                out_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in HOP_BY_HOP]
                writer.write(_status_line(resp.status_code, resp.reason_phrase))
                for k, v in out_headers:
                    writer.write(f"{k}: {v}\r\n".encode("latin-1", "replace"))
                writer.write(b"Transfer-Encoding: chunked\r\n\r\n")
                await writer.drain()
                async for chunk in resp.aiter_raw():
                    if not chunk:
                        continue
                    parser.feed(chunk)
                    writer.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                    await writer.drain()
                writer.write(b"0\r\n\r\n")
                await writer.drain()
                parser.close()
        except httpx.HTTPError as exc:
            rec.status = 502
            rec.refused = f"upstream error: {type(exc).__name__}"
            await _send_json(writer, 502, _error("cheat-index gateway: upstream error"))
            return False
        finally:
            rec.duration_s = round(time.time() - start, 3)
        rec.model = parser.model or model
        rec.prompt_tokens = parser.prompt_tokens
        rec.completion_tokens = parser.completion_tokens
        rec.cached_tokens = parser.cached_tokens
        rec.cost_reported = parser.cost
        rec.generation_id = parser.generation_id
        rec.cost_estimated = self._estimate(model, parser.prompt_tokens, parser.completion_tokens, parser.cached_tokens)
        return True

    # ---- admin ---------------------------------------------------------------------------------------------
    async def admin(self, method: str, path: str, headers: dict[str, str], body: bytes) -> tuple[int, Any]:
        host = headers.get("host", "").rsplit(":", 1)[0].lower()
        if host not in ADMIN_HOSTS or "origin" in headers:
            return 403, _error("forbidden")
        if not secrets.compare_digest(headers.get("x-admin-secret", ""), self.admin_secret):
            return 401, _error("admin secret required")
        parts = [p for p in path.split("/") if p]
        if parts == ["admin", "status"]:
            return 200, {"runs": len(self.runs), "spent_usd": round(self.spent_usd, 6), "cap_usd": self.global_cap_usd}
        if parts == ["admin", "key"] and method == "GET":
            resp = await self.client.get(
                f"{self.upstream}/v1/key", headers={"authorization": f"Bearer {self._api_key}"}
            )
            data = resp.json().get("data", {}) if resp.status_code == 200 else {}
            return resp.status_code, {k: data.get(k) for k in ("limit", "limit_remaining", "usage", "limit_reset")}
        if parts == ["admin", "runs"] and method == "POST":
            req = json.loads(body or b"{}")
            run = RunState(
                run_id=str(req["run_id"]),
                token=str(req["token"]),
                models=[str(m) for m in req.get("models") or []],
                max_cost_usd=float(req.get("max_cost_usd", 1.0)),
                max_tokens=int(req.get("max_tokens", 5_000_000)),
            )
            if run.token in self.by_token:
                return 409, _error("token already registered")
            self.runs[run.run_id] = run
            self.by_token[run.token] = run
            return 201, {"run_id": run.run_id}
        if len(parts) >= 3 and parts[:2] == ["admin", "runs"]:
            found = self.runs.get(parts[2])
            if found is None:
                return 404, _error("unknown run")
            if len(parts) == 3 and method == "GET":
                return 200, found.summary()
            if len(parts) == 3 and method == "DELETE":
                found.revoked = True
                self.by_token.pop(found.token, None)
                return 200, found.summary()
            if len(parts) == 4 and parts[3] == "reconcile" and method == "POST":
                await self.reconcile(found)
                return 200, found.summary()
        return 404, _error("unknown admin path")

    async def reconcile(self, run: RunState) -> None:
        for rec in run.requests:
            if not rec.generation_id or rec.cost_reconciled is not None or rec.status != 200:
                continue
            for attempt in range(4):
                resp = await self.client.get(
                    f"{self.upstream}/v1/generation",
                    params={"id": rec.generation_id},
                    headers={"authorization": f"Bearer {self._api_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json().get("data") or {}
                    cost = data.get("total_cost")
                    if isinstance(cost, int | float):
                        rec.cost_reconciled = float(cost)
                    if isinstance(data.get("provider_name"), str):
                        rec.provider = data["provider_name"]
                    break
                await asyncio.sleep(1.5 * (attempt + 1))


def _error(message: str) -> dict[str, Any]:
    return {"error": {"message": message, "type": "cheat_index_gateway"}}


def _status_line(code: int, reason: str) -> bytes:
    return f"HTTP/1.1 {code} {reason or 'OK'}\r\n".encode()


async def _send_json(writer: asyncio.StreamWriter, status: int, payload: Any) -> None:
    body = json.dumps(payload).encode()
    reasons = {200: "OK", 201: "Created", 401: "Unauthorized", 402: "Payment Required", 403: "Forbidden"}
    writer.write(_status_line(status, reasons.get(status, "Error")))
    writer.write(f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n".encode())
    writer.write(body)
    await writer.drain()


async def _read_request(reader: asyncio.StreamReader) -> tuple[str, str, dict[str, str], bytes] | None:
    try:
        head = await reader.readuntil(b"\r\n\r\n")
    except asyncio.IncompleteReadError:
        return None
    lines = head.decode("latin-1").split("\r\n")
    method, target, _version = lines[0].split(" ", 2)
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    body = b""
    if headers.get("transfer-encoding", "").lower() == "chunked":
        chunks = []
        while True:
            size_line = await reader.readuntil(b"\r\n")
            size = int(size_line.split(b";")[0].strip(), 16)
            if size == 0:
                await reader.readuntil(b"\r\n")
                break
            chunks.append(await reader.readexactly(size))
            await reader.readexactly(2)
            if sum(map(len, chunks)) > MAX_BODY:
                raise ValueError("body too large")
        body = b"".join(chunks)
        headers.pop("transfer-encoding")
    elif "content-length" in headers:
        n = int(headers["content-length"])
        if n > MAX_BODY:
            raise ValueError("body too large")
        body = await reader.readexactly(n)
    return method.upper(), target, headers, body


async def fetch_prices(client: httpx.AsyncClient, upstream: str = UPSTREAM) -> dict[str, Price]:
    resp = await client.get(f"{upstream}/v1/models")
    out: dict[str, Price] = {}
    for m in resp.json().get("data", []):
        p = m.get("pricing") or {}
        with contextlib.suppress(TypeError, ValueError):
            out[m["id"]] = Price(float(p.get("prompt", 0)), float(p.get("completion", 0)))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m cheat_index.runner.model_gateway")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--global-cap-usd", type=float, default=float("inf"))
    ap.add_argument("--spent-before-usd", type=float, default=0.0)
    ap.add_argument("--upstream", default=UPSTREAM)
    args = ap.parse_args(argv)
    key = os.environ.pop("OPENROUTER_API_KEY", "")
    secret = os.environ.pop("CHEAT_INDEX_ADMIN_SECRET", "")
    if not key or not secret:
        print("model_gateway: OPENROUTER_API_KEY and CHEAT_INDEX_ADMIN_SECRET must be set", file=sys.stderr)
        return 2

    async def run() -> None:
        gw = Gateway(
            key,
            secret,
            upstream=args.upstream,
            global_cap_usd=args.global_cap_usd,
            spent_before_usd=args.spent_before_usd,
        )
        with contextlib.suppress(httpx.HTTPError, ValueError):
            gw.prices = await fetch_prices(gw.client, args.upstream)
        server = await asyncio.start_server(gw.handle, args.host, args.port, limit=MAX_HEAD)
        print(f"model_gateway listening on {args.host}:{args.port} ({len(gw.prices)} prices)", flush=True)
        async with server:
            await server.serve_forever()

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
