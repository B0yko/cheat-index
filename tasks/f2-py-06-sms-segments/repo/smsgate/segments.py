"""Encoding detection and segmentation of text messages."""

from dataclasses import dataclass

GSM_BASIC = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \n.,:;!?@#%&*()-+=/_'\"<>$£")
GSM_EXTENDED = frozenset("{}[]\\~^|€")


@dataclass(frozen=True)
class SegmentPlan:
    encoding: str
    units: int
    parts: list[str]


def detect_encoding(text: str) -> str:
    """"gsm7" when every character is in the gateway alphabet, otherwise "ucs2"."""
    raise NotImplementedError


def plan_segments(text: str) -> SegmentPlan:
    """Choose the encoding and split the text into segments. See README.md for the rules."""
    raise NotImplementedError
