from pathlib import Path

from cheat_index.costs import estimate_per_run
from cheat_index.runner.commands import hooks_problem


def test_hooks_layout_is_checked_per_agent(tmp_path: Path) -> None:
    assert hooks_problem("claude-code", None) is None
    assert "claude-code.json" in (hooks_problem("claude-code", tmp_path) or "")
    (tmp_path / "claude-code.json").write_text("{}", encoding="utf-8")
    assert hooks_problem("claude-code", tmp_path) is None
    (tmp_path / "opencode-plugins").mkdir()
    assert hooks_problem("opencode", tmp_path) is None
    assert "codex-hooks.json" in (hooks_problem("codex", tmp_path) or "")
    assert "not supported" in (hooks_problem("copilot", tmp_path) or "")


def test_published_pairs_have_a_measured_cost() -> None:
    usd, basis = estimate_per_run("opencode", "deepseek/deepseek-v4-flash")
    assert usd is not None and 0 < usd < 0.05
    assert basis.startswith("measured over")
