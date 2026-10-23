"""Locations of the data that ships with the package (task suite, schemas, images, demo sample)."""

from __future__ import annotations

import os
from pathlib import Path

_PKG = Path(__file__).resolve().parent


def data_root() -> Path:
    """Return the directory that holds `tasks/`, `schemas/` and `images/`.

    An installed wheel carries them under `cheat_index/_data`; a source checkout keeps them at the repository root.
    """
    packaged = _PKG / "_data"
    if packaged.is_dir():
        return packaged
    return _PKG.parents[1]


def tasks_root() -> Path:
    override = os.environ.get("CHEAT_INDEX_TASKS")
    return Path(override) if override else data_root() / "tasks"


def schemas_root() -> Path:
    return data_root() / "schemas"


def images_root() -> Path:
    return data_root() / "images"


def package_data(*parts: str) -> Path:
    """A file shipped inside the package itself (templates, demo sample, price table)."""
    return _PKG.joinpath("data", *parts)
