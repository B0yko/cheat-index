"""Protecting {placeholders} from the translation engine."""


class PlaceholderError(ValueError):
    """A translated text lost, duplicated or invented a placeholder tag."""


def protect(text: str) -> tuple[str, list[str]]:
    """Replace placeholders by numbered tags. Returns the masked text and the original placeholders."""
    raise NotImplementedError


def restore(text: str, tokens: list[str]) -> str:
    """Put the original placeholders back into a translated text."""
    raise NotImplementedError
