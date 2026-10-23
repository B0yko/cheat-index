import pytest

from buildplan import CycleError, build_order, rebuild_set

DEPS = {
    "render-ui": ["libgrid", "libfont"],
    "libgrid": ["vecmath"],
    "libfont": ["vecmath", "zlite"],
    "installer": ["render-ui"],
}


def test_dependencies_come_first_and_ties_are_alphabetical():
    assert build_order(DEPS) == ["vecmath", "libgrid", "zlite", "libfont", "render-ui", "installer"]


def test_cycle_is_reported():
    with pytest.raises(CycleError) as info:
        build_order({"parser": ["lexer"], "lexer": ["tokens"], "tokens": ["parser"], "docs": []})
    assert info.value.cycle == ["lexer", "tokens", "parser", "lexer"]


def test_rebuild_set_follows_dependents():
    assert rebuild_set(DEPS, ["libfont"]) == ["libfont", "render-ui", "installer"]
