"""Client for the LingoForge translation API."""

import urllib.request
from collections.abc import Mapping

DEFAULT_BASE_URL = "https://api.lingoforge.example/v1"
KEY_VAR = "LINGOFORGE_API_KEY"


class MissingKeyError(RuntimeError):
    """No API key is available."""


class TranslateError(RuntimeError):
    """The translation service could not be used."""


def parse_response(body: str, expected: int) -> list[str]:
    """Read the texts out of a translate response."""
    raise NotImplementedError


class TranslateClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL) -> None:
        raise NotImplementedError

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "TranslateClient":
        """Build a client from LINGOFORGE_API_KEY."""
        raise NotImplementedError

    def build_request(self, masked_texts: list[str], target: str, source: str | None = None) -> urllib.request.Request:
        raise NotImplementedError

    def translate(self, texts: list[str], target: str, source: str | None = None, *, timeout: float = 30.0) -> list[str]:
        raise NotImplementedError
