"""Parsing of the report that pdfsignctl prints."""

from dataclasses import dataclass


class ReportError(ValueError):
    """The tool output is not a valid report."""


@dataclass(frozen=True)
class SignReport:
    status: str
    signer: str = ""
    signed_at: str = ""
    digest: str = ""
    output: str = ""

    @property
    def ok(self) -> bool:
        raise NotImplementedError


def parse_report(text: str) -> SignReport:
    """Parse the stdout of pdfsignctl. See README.md for the rules."""
    raise NotImplementedError
