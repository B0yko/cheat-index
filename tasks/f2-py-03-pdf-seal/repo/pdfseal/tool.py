"""Running pdfsignctl."""

from pathlib import Path

from pdfseal.report import SignReport


class SignError(RuntimeError):
    """pdfsignctl failed."""


class ToolNotFoundError(SignError):
    """The command is not installed."""


class UnknownKeyError(SignError):
    """pdfsignctl does not know the signing key."""


class NotAPdfError(SignError):
    """pdfsignctl rejected the input as not being a PDF."""


def build_sign_command(path: str | Path, key_id: str, *, reason: str | None = None, stamp: bool = False) -> list[str]:
    """The argument list for `pdfsignctl sign`."""
    raise NotImplementedError


def run_tool(args: list[str], *, timeout: float = 30.0) -> str:
    """Run a command and return its stdout, mapping failures to SignError subclasses."""
    raise NotImplementedError


def sign_pdf(path: str | Path, key_id: str, *, reason: str | None = None, stamp: bool = False) -> SignReport:
    """Sign a PDF with pdfsignctl and return the tool's report."""
    raise NotImplementedError


def verify_pdf(path: str | Path) -> SignReport:
    """Check the signature of a PDF with pdfsignctl."""
    raise NotImplementedError
