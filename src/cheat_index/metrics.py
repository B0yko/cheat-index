"""Rates, intervals and ranking.

* Point estimates are ratios of flagged runs to valid runs (errored runs are excluded and reported).
* Intervals come from a cluster bootstrap over tasks (runs of one task are correlated): resample tasks with
  replacement, pool their runs, recompute the ratio; 10,000 resamples, fixed seed, percentile 95% interval.
* Detail pages show Wilson intervals on per-family k/N.
* Rank groups: sort by the ACI point estimate (lower is better). The first configuration opens a group; each next
  configuration joins the current group unless its interval does not overlap the interval of the group's first
  member, in which case it opens a new group.
* Ordering text: two configurations are put in order in prose only when a paired task-cluster bootstrap of their
  ACI difference (same tasks, 10,000 resamples) gives a 95% interval that excludes zero.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

import numpy as np

RESAMPLES = 10_000
SEED = 20261023
ACI_FAMILIES = ("F1", "F2", "F3")


@dataclass(frozen=True)
class Interval:
    point: float | None
    lo: float | None
    hi: float | None
    k: int
    n: int

    def overlaps(self, other: Interval) -> bool:
        if None in (self.lo, self.hi, other.lo, other.hi):
            return True
        assert self.lo is not None and self.hi is not None and other.lo is not None and other.hi is not None
        return self.lo <= other.hi and other.lo <= self.hi

    def to_dict(self) -> dict[str, float | int | None]:
        return {"point": self.point, "lo": self.lo, "hi": self.hi, "k": self.k, "n": self.n}


@dataclass(frozen=True)
class Obs:
    """One valid run reduced to what a rate needs: its task cluster and whether it is flagged."""

    task: str
    flagged: bool


def _clusters(obs: Sequence[Obs]) -> tuple[list[str], np.ndarray, np.ndarray]:
    k: dict[str, int] = defaultdict(int)
    n: dict[str, int] = defaultdict(int)
    for o in obs:
        n[o.task] += 1
        k[o.task] += int(o.flagged)
    tasks = sorted(n)
    return tasks, np.array([k[t] for t in tasks], dtype=float), np.array([n[t] for t in tasks], dtype=float)


def cluster_bootstrap(obs: Sequence[Obs], *, resamples: int = RESAMPLES, seed: int = SEED) -> Interval:
    tasks, k, n = _clusters(obs)
    total_k, total_n = int(k.sum()), int(n.sum())
    if total_n == 0:
        return Interval(None, None, None, 0, 0)
    point = total_k / total_n
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(tasks), size=(resamples, len(tasks)))
    ratios = k[idx].sum(axis=1) / n[idx].sum(axis=1)
    lo, hi = np.percentile(ratios, [2.5, 97.5])
    return Interval(point, float(lo), float(hi), total_k, total_n)


def wilson(k: int, n: int, z: float = 1.959963984540054) -> Interval:
    if n == 0:
        return Interval(None, None, None, k, n)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return Interval(p, max(0.0, centre - half), min(1.0, centre + half), k, n)


@dataclass(frozen=True)
class PairedDiff:
    diff: float | None
    lo: float | None
    hi: float | None
    tasks: int

    @property
    def excludes_zero(self) -> bool:
        return self.lo is not None and self.hi is not None and (self.lo > 0 or self.hi < 0)


def paired_bootstrap(a: Sequence[Obs], b: Sequence[Obs], *, resamples: int = RESAMPLES, seed: int = SEED) -> PairedDiff:
    """Bootstrap of rate(a) - rate(b) over the tasks both configurations ran (paired by task)."""
    ta, ka, na = _clusters(a)
    tb, kb, nb = _clusters(b)
    common = sorted(set(ta) & set(tb))
    if not common:
        return PairedDiff(None, None, None, 0)
    ia = [ta.index(t) for t in common]
    ib = [tb.index(t) for t in common]
    ka, na, kb, nb = ka[ia], na[ia], kb[ib], nb[ib]
    diff = ka.sum() / na.sum() - kb.sum() / nb.sum()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(common), size=(resamples, len(common)))
    diffs = ka[idx].sum(axis=1) / na[idx].sum(axis=1) - kb[idx].sum(axis=1) / nb[idx].sum(axis=1)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return PairedDiff(float(diff), float(lo), float(hi), len(common))


def rank_groups(items: Sequence[tuple[str, Interval]]) -> dict[str, int]:
    """Greedy rank groups over configurations already sorted by point estimate (best first)."""
    groups: dict[str, int] = {}
    leader: Interval | None = None
    group = 0
    for name, iv in items:
        if leader is None or not iv.overlaps(leader):
            group += 1
            leader = iv
        groups[name] = group
    return groups


def sort_key(iv: Interval) -> tuple[float, float]:
    return (math.inf if iv.point is None else iv.point, math.inf if iv.hi is None else iv.hi)


def rate(
    runs: Iterable[dict[str, object]], families: Iterable[str], flag: Callable[[dict[str, object]], bool]
) -> Interval:
    fams = set(families)
    obs = [Obs(str(r["task_id"]), flag(r)) for r in runs if r["family"] in fams]
    return cluster_bootstrap(obs)


def cohen_kappa(pairs: Sequence[tuple[object, object]]) -> float | None:
    """Cohen's kappa for two raters' labels on the same items."""
    from collections import Counter

    n = len(pairs)
    if n == 0:
        return None
    observed = sum(a == b for a, b in pairs) / n
    ca = Counter(a for a, _ in pairs)
    cb = Counter(b for _, b in pairs)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)
