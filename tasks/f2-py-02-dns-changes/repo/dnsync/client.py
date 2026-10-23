"""Client for the platform DNS service."""

import urllib.request
from collections.abc import Mapping

from dnsync.records import Change

DEFAULT_BASE_URL = "https://dns.platform.internal/v2"
TOKEN_VAR = "DNS_API_TOKEN"


class MissingCredentialsError(RuntimeError):
    """No API token is available."""


class DnsError(RuntimeError):
    """The DNS service could not be used."""


class DnsClient:
    def __init__(self, token: str, base_url: str = DEFAULT_BASE_URL) -> None:
        raise NotImplementedError

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "DnsClient":
        """Build a client from DNS_API_TOKEN (and optionally DNS_API_URL)."""
        raise NotImplementedError

    def build_request(self, zone: str, changes: list[Change]) -> urllib.request.Request:
        raise NotImplementedError

    def push(self, zone: str, changes: list[Change], *, timeout: float = 10.0) -> dict:
        raise NotImplementedError
