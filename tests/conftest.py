"""Shared fixtures. Unit tests never reach the network: only loopback and Unix sockets are allowed."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Iterator
from typing import Any

import pytest

_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
_real_getaddrinfo = socket.getaddrinfo


def _is_local(address: Any) -> bool:
    if isinstance(address, str | bytes):
        return True  # Unix domain socket
    host = address[0]
    if host in ("localhost", ""):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class NetworkBlocked(RuntimeError):
    pass


@pytest.fixture(autouse=True)
def _block_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    if request.node.get_closest_marker("docker"):
        yield
        return

    def guarded_connect(self: socket.socket, address: Any) -> Any:
        if not _is_local(address):
            raise NetworkBlocked(f"unit tests may not connect to {address!r}")
        return _real_connect(self, address)

    def guarded_connect_ex(self: socket.socket, address: Any) -> Any:
        if not _is_local(address):
            raise NetworkBlocked(f"unit tests may not connect to {address!r}")
        return _real_connect_ex(self, address)

    def guarded_getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        if host not in (None, "localhost", "127.0.0.1", "::1", b"localhost"):
            try:
                ipaddress.ip_address(host)
            except ValueError:
                raise NetworkBlocked(f"unit tests may not resolve {host!r}") from None
        return _real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    yield
