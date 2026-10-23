"""Client for the freight rate service."""

import urllib.request
from collections.abc import Callable

from freight.quote import Quote, QuoteError

DEFAULT_BASE_URL = "https://rates.freight.internal/v3"

Transport = Callable[[urllib.request.Request, float], bytes]


class NoRouteError(QuoteError):
    """No carrier serves the requested route."""


def urlopen_transport(request: urllib.request.Request, timeout: float) -> bytes:
    """Default transport: perform the request with urllib."""
    raise NotImplementedError


class FreightClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, transport: Transport | None = None) -> None:
        raise NotImplementedError

    def quote(self, origin: str, destination: str, weight_kg: int, *, timeout: float = 10.0) -> Quote:
        """Ask the rate service for a quote."""
        raise NotImplementedError
