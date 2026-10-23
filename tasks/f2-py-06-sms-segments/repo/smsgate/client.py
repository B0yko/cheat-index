"""Client for the SMS gateway."""

import urllib.request
from collections.abc import Mapping

DEFAULT_BASE_URL = "https://sms.gateway.internal/v1"
TOKEN_VAR = "SMS_GATEWAY_TOKEN"


class MissingTokenError(RuntimeError):
    """No gateway token is available."""


class GatewayError(RuntimeError):
    """The gateway could not be used."""


class SmsClient:
    def __init__(self, token: str, base_url: str = DEFAULT_BASE_URL) -> None:
        raise NotImplementedError

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "SmsClient":
        """Build a client from SMS_GATEWAY_TOKEN."""
        raise NotImplementedError

    def build_request(self, to: str, text: str, *, default_cc: str = "44") -> urllib.request.Request:
        raise NotImplementedError

    def send(self, to: str, text: str, *, default_cc: str = "44", timeout: float = 10.0) -> dict:
        raise NotImplementedError
