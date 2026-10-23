"""The cheat_index package as copied into infrastructure containers (gateway, proxy, verification)."""

from __future__ import annotations

from pathlib import Path

import cheat_index


def package_dir() -> Path:
    return Path(cheat_index.__file__).resolve().parent


# Never copied into containers: packaged task data (it includes hidden checks) and demo recordings.
EXCLUDED = ("_data", "data/demo")
