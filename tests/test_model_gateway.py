from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import httpx

from cheat_index.runner.model_gateway import Gateway, Price, UsageParser

REAL_KEY = "sk-or-v1-real-key-for-tests"
SECRET = "admin-secret"

CHAT_SSE = (
    b'data: {"id":"gen-1","model":"qwen/qwen3-coder","choices":[{"delta":{"content":"hi"}}]}\n\n'
    b'data: {"id":"gen-1","choices":[],"usage":{"prompt_tokens":1000,"completion_tokens":50,"cost":0.0012}}\n\n'
    b"data: [DONE]\n\n"
)
ANTHROPIC_SSE = (
    b'event: message_start\ndata: {"type":"message_start","message":{"id":"gen-2","model":"z-ai/glm-4.6",'
    b'"usage":{"input_tokens":200,"cache_read_input_tokens":800,"output_tokens":1}}}\n\n'
    b'event: message_delta\ndata: {"type":"message_delta","usage":{"output_tokens":40}}\n\n'
)


class Chunks(httpx.AsyncByteStream):
    """Delivers a body in small pieces, like a real streamed response."""

    def __init__(self, data: bytes) -> None:
        self.data = data

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for i in range(0, len(self.data), 17):
            yield self.data[i : i + 17]


def sse(data: bytes) -> httpx.Response:
    return httpx.Response(200, stream=Chunks(data), headers={"content-type": "text/event-stream"})


def upstream_handler(seen: list[httpx.Request]) -> Callable[[httpx.Request], httpx.Response]:
    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.headers["authorization"] == f"Bearer {REAL_KEY}"
        assert "x-api-key" not in request.headers
        if request.url.path == "/api/v1/key":
            return httpx.Response(200, json={"data": {"limit": 90, "limit_remaining": 70.5, "label": REAL_KEY}})
        if request.url.path == "/api/v1/generation":
            return httpx.Response(200, json={"data": {"total_cost": 0.002}})
        if request.url.path == "/api/v1/messages":
            return sse(ANTHROPIC_SSE)
        return sse(CHAT_SSE)

    return handle


def run_with_gateway(scenario: Callable[[Gateway, httpx.AsyncClient], Awaitable[Any]], **kw: Any) -> Any:
    async def main() -> Any:
        seen: list[httpx.Request] = []
        gw = Gateway(
            REAL_KEY,
            SECRET,
            transport=httpx.MockTransport(upstream_handler(seen)),
            prices={"z-ai/glm-4.6": Price(1e-6, 2e-6)},
            **kw,
        )
        server = await asyncio.start_server(gw.handle, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}") as client:
            result = await scenario(gw, client)
        server.close()
        return result

    return asyncio.run(main())


ADMIN = {"x-admin-secret": SECRET}


async def register(client: httpx.AsyncClient, run_id: str, token: str, **caps: Any) -> None:
    body = {"run_id": run_id, "token": token, "models": ["qwen/qwen3-coder", "z-ai/glm-4.6"], **caps}
    r = await client.post("/admin/runs", json=body, headers=ADMIN)
    assert r.status_code == 201


def test_unknown_token_is_rejected() -> None:
    async def scenario(gw: Gateway, client: httpx.AsyncClient) -> httpx.Response:
        return await client.post(
            "/api/v1/chat/completions", json={"model": "x"}, headers={"authorization": "Bearer nope"}
        )

    assert run_with_gateway(scenario).status_code == 401


def test_streams_through_and_records_reported_cost() -> None:
    async def scenario(gw: Gateway, client: httpx.AsyncClient) -> tuple[bytes, dict[str, Any]]:
        await register(client, "r1", "ci-token-1")
        r = await client.post(
            "/api/v1/chat/completions",
            json={"model": "qwen/qwen3-coder", "stream": True},
            headers={"authorization": "Bearer ci-token-1"},
        )
        usage = (await client.get("/admin/runs/r1", headers=ADMIN)).json()
        return r.content, usage

    body, usage = run_with_gateway(scenario)
    assert body == CHAT_SSE
    assert REAL_KEY.encode() not in body
    assert usage["prompt_tokens"] == 1000 and usage["completion_tokens"] == 50
    assert usage["cost_usd"] == 0.0012 and usage["cost_source"] == "provider"
    assert usage["log"][0]["generation_id"] == "gen-1"


def test_anthropic_stream_usage_and_estimate_then_reconcile() -> None:
    async def scenario(gw: Gateway, client: httpx.AsyncClient) -> tuple[dict[str, Any], dict[str, Any]]:
        await register(client, "r2", "ci-token-2")
        await client.post(
            "/api/v1/messages", json={"model": "z-ai/glm-4.6", "stream": True}, headers={"x-api-key": "ci-token-2"}
        )
        before = (await client.get("/admin/runs/r2", headers=ADMIN)).json()
        after = (await client.post("/admin/runs/r2/reconcile", headers=ADMIN)).json()
        return before, after

    before, after = run_with_gateway(scenario)
    assert before["prompt_tokens"] == 1000 and before["completion_tokens"] == 40
    assert before["cached_tokens"] == 800
    assert before["cost_source"] == "estimate"
    assert abs(before["cost_usd"] - (1000 * 1e-6 + 40 * 2e-6)) < 1e-12
    assert after["cost_usd"] == 0.002 and after["cost_source"] == "provider"


def test_cost_cap_cuts_off_run() -> None:
    async def scenario(gw: Gateway, client: httpx.AsyncClient) -> list[int]:
        await register(client, "r3", "ci-token-3", max_cost_usd=0.001)
        codes = []
        for _ in range(2):
            r = await client.post(
                "/api/v1/chat/completions",
                json={"model": "qwen/qwen3-coder"},
                headers={"authorization": "Bearer ci-token-3"},
            )
            codes.append(r.status_code)
        return codes

    assert run_with_gateway(scenario) == [200, 402]


def test_global_cap_and_model_allow_list() -> None:
    async def scenario(gw: Gateway, client: httpx.AsyncClient) -> list[int]:
        await register(client, "r4", "ci-token-4")
        h = {"authorization": "Bearer ci-token-4"}
        wrong_model = await client.post("/api/v1/chat/completions", json={"model": "openai/gpt-5"}, headers=h)
        ok = await client.post("/api/v1/chat/completions", json={"model": "qwen/qwen3-coder"}, headers=h)
        over = await client.post("/api/v1/chat/completions", json={"model": "qwen/qwen3-coder"}, headers=h)
        return [wrong_model.status_code, ok.status_code, over.status_code]

    assert run_with_gateway(scenario, global_cap_usd=1.0, spent_before_usd=0.9995) == [402, 200, 402]


def test_admin_requires_secret_loopback_host_and_no_origin() -> None:
    async def scenario(gw: Gateway, client: httpx.AsyncClient) -> list[int]:
        a = await client.get("/admin/status")
        b = await client.get("/admin/status", headers={**ADMIN, "origin": "http://evil.example"})
        c = await client.get("/admin/status", headers={**ADMIN, "host": "evil.example"})
        d = await client.get("/admin/status", headers=ADMIN)
        return [a.status_code, b.status_code, c.status_code, d.status_code]

    assert run_with_gateway(scenario) == [401, 403, 403, 200]


def test_key_status_never_returns_the_key_and_revoke() -> None:
    async def scenario(gw: Gateway, client: httpx.AsyncClient) -> tuple[str, int]:
        key = (await client.get("/admin/key", headers=ADMIN)).text
        await register(client, "r5", "ci-token-5")
        await client.delete("/admin/runs/r5", headers=ADMIN)
        r = await client.post("/api/v1/chat/completions", json={}, headers={"authorization": "Bearer ci-token-5"})
        return key, r.status_code

    key, code = run_with_gateway(scenario)
    assert REAL_KEY not in key and json.loads(key)["limit_remaining"] == 70.5
    assert code == 401


def test_usage_parser_plain_json_responses_api() -> None:
    p = UsageParser(streaming=False)
    p.feed(json.dumps({"id": "gen-9", "model": "m", "usage": {"input_tokens": 10, "output_tokens": 3}}).encode())
    p.close()
    assert (p.prompt_tokens, p.completion_tokens, p.generation_id) == (10, 3, "gen-9")
