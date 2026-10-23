"""Allow-listing HTTP forward proxy (CONNECT and absolute-form HTTP) that logs every connection attempt.

Agent containers sit on an internal Docker network; this proxy is their only route out. It permits the hosts the
agent configuration declares (normally only the model gateway), refuses everything else with 403 and writes one
JSON line per attempt: time, client, method, host, port and whether it was allowed.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import fnmatch
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO
from urllib.parse import SplitResult, urlsplit

MAX_HEAD = 64 * 1024
CONNECT_TIMEOUT = 10.0
HOP_BY_HOP = {"proxy-connection", "proxy-authorization", "connection", "keep-alive"}


@dataclass(frozen=True)
class Rule:
    host: str
    port: int | None

    @classmethod
    def parse(cls, text: str) -> Rule:
        host, sep, port = text.strip().rpartition(":")
        if sep and port.isdigit() and host:
            return cls(host.lower(), int(port))
        return cls(text.strip().lower(), None)

    def matches(self, host: str, port: int) -> bool:
        return fnmatch.fnmatchcase(host.lower(), self.host) and (self.port is None or self.port == port)


@dataclass
class EgressProxy:
    rules: list[Rule]
    log: TextIO | None = None
    attempts: list[dict[str, object]] = field(default_factory=list)

    def allowed(self, host: str, port: int) -> bool:
        return any(r.matches(host, port) for r in self.rules)

    def record(self, client: str, method: str, host: str, port: int, allowed: bool, note: str = "") -> None:
        entry: dict[str, object] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{int(time.time() * 1000) % 1000:03d}Z",
            "client": client,
            "method": method,
            "host": host,
            "port": port,
            "allowed": allowed,
        }
        if note:
            entry["note"] = note
        self.attempts.append(entry)
        if self.log is not None:
            self.log.write(json.dumps(entry) + "\n")
            self.log.flush()

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        client = str(peer[0]) if peer else "?"
        try:
            head = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=30)
        except (asyncio.IncompleteReadError, asyncio.LimitOverrunError, TimeoutError, ConnectionError):
            writer.close()
            return
        try:
            lines = head.decode("latin-1").split("\r\n")
            method, target, version = lines[0].split(" ", 2)
        except ValueError:
            await self._reply(writer, 400, "Bad Request")
            return
        if method.upper() == "CONNECT":
            host, _, port_text = target.rpartition(":")
            host = host.strip("[]")
            port = int(port_text) if port_text.isdigit() else 443
            await self._connect(reader, writer, client, host, port)
            return
        parts = urlsplit(target)
        if parts.scheme != "http" or not parts.hostname:
            self.record(client, method, parts.hostname or target[:100], parts.port or 0, False, "not a proxy request")
            await self._reply(writer, 400, "Bad Request")
            return
        await self._forward(reader, writer, client, method, parts, version, lines[1:])

    async def _reply(self, writer: asyncio.StreamWriter, code: int, reason: str) -> None:
        body = f"egress refused by cheat-index proxy: {reason}\n".encode()
        writer.write(
            f"HTTP/1.1 {code} {reason}\r\nContent-Type: text/plain\r\nContent-Length: {len(body)}\r\n"
            "Connection: close\r\n\r\n".encode()
            + body
        )
        with contextlib.suppress(ConnectionError):
            await writer.drain()
        writer.close()

    async def _open(self, host: str, port: int) -> tuple[asyncio.StreamReader, asyncio.StreamWriter] | None:
        try:
            return await asyncio.wait_for(asyncio.open_connection(host, port), timeout=CONNECT_TIMEOUT)
        except (OSError, TimeoutError):
            return None

    async def _connect(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client: str, host: str, port: int
    ) -> None:
        ok = self.allowed(host, port)
        self.record(client, "CONNECT", host, port, ok)
        if not ok:
            await self._reply(writer, 403, "Forbidden")
            return
        upstream = await self._open(host, port)
        if upstream is None:
            await self._reply(writer, 502, "Bad Gateway")
            return
        writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        await writer.drain()
        await _pipe_both(reader, writer, *upstream)

    async def _forward(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        client: str,
        method: str,
        parts: SplitResult,
        version: str,
        header_lines: list[str],
    ) -> None:
        host = parts.hostname or ""
        port = parts.port or 80
        ok = self.allowed(host, port)
        self.record(client, method, host, port, ok)
        if not ok:
            await self._reply(writer, 403, "Forbidden")
            return
        upstream = await self._open(host, port)
        if upstream is None:
            await self._reply(writer, 502, "Bad Gateway")
            return
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        kept = [h for h in header_lines if h and h.split(":", 1)[0].strip().lower() not in HOP_BY_HOP]
        up_reader, up_writer = upstream
        up_writer.write((f"{method} {path} {version}\r\n" + "".join(h + "\r\n" for h in kept)).encode("latin-1"))
        up_writer.write(b"Connection: close\r\n\r\n")
        await up_writer.drain()
        await _pipe_both(reader, writer, up_reader, up_writer)


async def _pipe(src: asyncio.StreamReader, dst: asyncio.StreamWriter) -> None:
    try:
        while data := await src.read(65536):
            dst.write(data)
            await dst.drain()
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        with contextlib.suppress(Exception):
            if dst.can_write_eof():
                dst.write_eof()


async def _pipe_both(
    r1: asyncio.StreamReader, w1: asyncio.StreamWriter, r2: asyncio.StreamReader, w2: asyncio.StreamWriter
) -> None:
    await asyncio.gather(_pipe(r1, w2), _pipe(r2, w1))
    for w in (w1, w2):
        with contextlib.suppress(Exception):
            w.close()


async def serve(proxy: EgressProxy, host: str, port: int) -> asyncio.Server:
    return await asyncio.start_server(proxy.handle, host, port, limit=MAX_HEAD)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m cheat_index.runner.egress_proxy")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=3128)
    ap.add_argument("--allow", action="append", default=[], help="host, host:port or *.domain (repeatable)")
    ap.add_argument("--log", type=Path, help="JSON Lines log of every attempt (default: stdout)")
    args = ap.parse_args(argv)
    log: TextIO = args.log.open("a", encoding="utf-8") if args.log else sys.stdout
    proxy = EgressProxy([Rule.parse(a) for a in args.allow], log)

    async def run() -> None:
        server = await serve(proxy, args.host, args.port)
        async with server:
            await server.serve_forever()

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
