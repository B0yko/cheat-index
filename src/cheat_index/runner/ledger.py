"""A cost ledger shared by every run of a results directory: it stops starting runs before the budget is reached.

Each run reserves its per-run cap before it starts; the reservation is replaced by the run's measured cost when it
finishes. A run may start only while spent + reserved + its own cap stays at or below the stop line.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Ledger:
    path: Path
    budget_usd: float
    stop_at_usd: float
    entries: list[dict[str, Any]] = field(default_factory=list)
    reserved: dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def open(cls, path: Path, budget_usd: float, stop_at_usd: float | None = None) -> Ledger:
        stop = stop_at_usd if stop_at_usd is not None else budget_usd
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(path, float(data.get("budget_usd", budget_usd)), float(data.get("stop_at_usd", stop)),
                       list(data.get("entries", [])))  # fmt: skip
        return cls(path, budget_usd, stop)

    @property
    def spent_usd(self) -> float:
        return round(sum(float(e["cost_usd"]) for e in self.entries), 6)

    def can_start(self, run_key: str, cap_usd: float) -> bool:
        with self._lock:
            projected = self.spent_usd + sum(self.reserved.values()) + cap_usd
            if projected > self.stop_at_usd:
                return False
            self.reserved[run_key] = cap_usd
            return True

    def record(self, run_key: str, config: str, cost_usd: float, source: str) -> None:
        with self._lock:
            self.reserved.pop(run_key, None)
            self.entries.append(
                {"run": run_key, "config": config, "cost_usd": round(cost_usd, 6), "source": source,
                 "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            )  # fmt: skip
            self._save()

    def release(self, run_key: str) -> None:
        with self._lock:
            self.reserved.pop(run_key, None)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(
                {"budget_usd": self.budget_usd, "stop_at_usd": self.stop_at_usd, "spent_usd": self.spent_usd,
                 "entries": self.entries},
                indent=1,
            ),
            encoding="utf-8",
        )  # fmt: skip
        tmp.replace(self.path)
