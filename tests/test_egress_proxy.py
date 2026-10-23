from __future__ import annotations

import asyncio
import io
import json

from cheat_index.runner.egress_proxy import EgressProxy, Rule, serve


async def _upstream() -> tuple[asyncio.Server, int]:
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readuntil(b"\r\n\r\n")
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\nConnection: close\r\n\r\nhello")
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


async def _request(port: int, raw: bytes) -> bytes:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(raw)
    await writer.drain()
    data = await asyncio.wait_for(reader.read(), timeout=5)
    writer.close()
    return data


def test_rule_parsing_and_matching() -> None:
    assert Rule.parse("gateway:8080").matches("gateway", 8080)
    assert not Rule.parse("gateway:8080").matches("gateway", 80)
    assert Rule.parse("*.example.org").matches("api.example.org", 443)
    assert not Rule.parse("*.example.org").matches("example.com", 443)


def test_connect_allowed_refused_and_logged() -> None:
    async def scenario() -> tuple[bytes, bytes, list[dict[str, object]], str]:
        upstream, up_port = await _upstream()
        log = io.StringIO()
        proxy = EgressProxy([Rule("127.0.0.1", up_port)], log)
        server = await serve(proxy, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        # Allowed CONNECT, then plain HTTP through the tunnel.
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(f"CONNECT 127.0.0.1:{up_port} HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n".encode())
        await writer.drain()
        established = await reader.readuntil(b"\r\n\r\n")
        writer.write(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
        await writer.drain()
        tunnelled = await asyncio.wait_for(reader.read(), timeout=5)
        writer.close()
        refused = await _request(port, b"CONNECT example.com:443 HTTP/1.1\r\nHost: example.com:443\r\n\r\n")
        server.close()
        upstream.close()
        return established + tunnelled, refused, proxy.attempts, log.getvalue()

    ok, refused, attempts, log = asyncio.run(scenario())
    assert ok.startswith(b"HTTP/1.1 200 Connection Established") and ok.endswith(b"hello")
    assert refused.startswith(b"HTTP/1.1 403")
    assert [(a["host"], a["allowed"]) for a in attempts] == [("127.0.0.1", True), ("example.com", False)]
    lines = [json.loads(line) for line in log.splitlines()]
    assert lines[1]["host"] == "example.com" and lines[1]["port"] == 443 and lines[1]["method"] == "CONNECT"


def test_plain_http_forward_and_refusal() -> None:
    async def scenario() -> tuple[bytes, bytes, bytes]:
        upstream, up_port = await _upstream()
        proxy = EgressProxy([Rule("127.0.0.1", up_port)])
        server = await serve(proxy, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        ok = await _request(port, f"GET http://127.0.0.1:{up_port}/x HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n".encode())
        bad = await _request(port, b"GET http://example.com/ HTTP/1.1\r\nHost: example.com\r\n\r\n")
        origin_form = await _request(port, b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        server.close()
        upstream.close()
        return ok, bad, origin_form

    ok, bad, origin_form = asyncio.run(scenario())
    assert ok.startswith(b"HTTP/1.1 200") and ok.endswith(b"hello")
    assert bad.startswith(b"HTTP/1.1 403")
    assert origin_form.startswith(b"HTTP/1.1 400")
