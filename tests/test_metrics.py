from __future__ import annotations

import pytest

from cheat_index.metrics import Interval, Obs, cluster_bootstrap, cohen_kappa, paired_bootstrap, rank_groups, wilson


def obs(spec: dict[str, list[int]]) -> list[Obs]:
    return [Obs(task, bool(v)) for task, values in spec.items() for v in values]


def iv(lo: float, hi: float) -> Interval:
    return Interval((lo + hi) / 2, lo, hi, 0, 10)


def test_wilson_matches_reference_values() -> None:
    w = wilson(5, 10)
    assert w.point == 0.5
    assert w.lo == pytest.approx(0.2366, abs=1e-4) and w.hi == pytest.approx(0.7634, abs=1e-4)
    z = wilson(0, 20)
    assert z.lo == 0.0 and z.hi == pytest.approx(0.1611, abs=1e-4)
    assert wilson(0, 0).point is None


def test_cluster_bootstrap_degenerate_and_deterministic() -> None:
    all_flagged = cluster_bootstrap(obs({f"t{i}": [1, 1] for i in range(10)}))
    assert all_flagged.point == 1.0 and all_flagged.hi == 1.0
    assert all_flagged.lo == pytest.approx(wilson(20, 20).lo)  # Wilson, not a collapsed bootstrap
    none_flagged = cluster_bootstrap(obs({f"t{i}": [0, 0] for i in range(10)}))
    assert none_flagged.lo == 0.0 and none_flagged.hi == pytest.approx(wilson(0, 20).hi)
    data = obs({f"t{i}": [i % 3 == 0, i % 2 == 0] for i in range(30)})
    a, b = cluster_bootstrap(data), cluster_bootstrap(data)
    assert a == b
    assert a.lo is not None and a.hi is not None and a.lo <= a.point <= a.hi  # type: ignore[operator]
    assert (a.k, a.n) == (25, 60)
    assert cluster_bootstrap([]).point is None


def test_cluster_bootstrap_is_wider_when_runs_cluster_by_task() -> None:
    # Same overall rate (50%), but in the clustered set each task is all-or-nothing.
    clustered = obs({f"t{i}": [i % 2] * 4 for i in range(20)})
    mixed = obs({f"t{i}": [0, 1, 0, 1] for i in range(20)})
    c, m = cluster_bootstrap(clustered), cluster_bootstrap(mixed)
    assert c.point == m.point == 0.5
    assert (c.hi - c.lo) > (m.hi - m.lo)  # type: ignore[operator]


def test_rank_groups_compare_with_the_group_leader() -> None:
    items = [("A", iv(0.10, 0.20)), ("B", iv(0.15, 0.30)), ("C", iv(0.25, 0.40)), ("D", iv(0.50, 0.60))]
    # B overlaps A (joins group 1); C overlaps B but not the leader A, so it opens group 2; D opens group 3.
    assert rank_groups(items) == {"A": 1, "B": 1, "C": 2, "D": 3}


def test_rank_groups_single_and_all_overlapping() -> None:
    assert rank_groups([("A", iv(0.1, 0.5))]) == {"A": 1}
    items = [("A", iv(0.1, 0.5)), ("B", iv(0.2, 0.6)), ("C", iv(0.4, 0.9))]
    assert rank_groups(items) == {"A": 1, "B": 1, "C": 1}


def test_paired_bootstrap_orders_only_clear_differences() -> None:
    a = obs({f"t{i}": [1, 1] for i in range(30)})
    b = obs({f"t{i}": [0, 0] for i in range(30)})
    clear = paired_bootstrap(a, b)
    assert clear.diff == 1.0 and clear.excludes_zero
    same = paired_bootstrap(a, a)
    assert same.diff == 0.0 and not same.excludes_zero
    close_a = obs({f"t{i}": [i % 2] for i in range(30)})
    close_b = obs({f"t{i}": [(i + 1) % 2 if i < 2 else i % 2] for i in range(30)})
    assert not paired_bootstrap(close_a, close_b).excludes_zero


def test_paired_bootstrap_uses_common_tasks_only() -> None:
    a = obs({"t1": [1], "t2": [1], "only_a": [0]})
    b = obs({"t1": [0], "t2": [0], "only_b": [1]})
    p = paired_bootstrap(a, b)
    assert p.tasks == 2 and p.diff == 1.0
    assert paired_bootstrap(obs({"x": [1]}), obs({"y": [1]})).diff is None


def test_cohen_kappa() -> None:
    assert cohen_kappa([(1, 1), (0, 0), (1, 1), (0, 0)]) == 1.0
    # 70% observed agreement, 50% expected by chance -> 0.4
    pairs = [(1, 1)] * 35 + [(0, 0)] * 35 + [(1, 0)] * 15 + [(0, 1)] * 15
    assert cohen_kappa(pairs) == pytest.approx(0.4)
    assert cohen_kappa([]) is None
