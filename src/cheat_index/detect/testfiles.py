"""Per-language rules that classify repository paths as tests, test configuration, source or other files."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

TEST = "test"
TEST_CONFIG = "test_config"
SOURCE = "source"
OTHER = "other"

_TEST_DIRS = {"tests", "test", "__tests__", "__snapshots__", "snapshots", "spec"}
_PY_TEST_NAME = re.compile(r"^(test_.*\.py|.*_test\.py|conftest\.py)$")
_TS_TEST_NAME = re.compile(r"^.*\.(test|spec)\.(ts|tsx|mts|cts|js|jsx|mjs|cjs)$")
_SNAPSHOT_NAME = re.compile(r"^.*\.snap$")
_CONFIG_NAMES = {
    "pytest.ini",
    "tox.ini",
    "setup.cfg",
    "pyproject.toml",
    "conftest.py",
    "noxfile.py",
    "sitecustomize.py",
    "usercustomize.py",
    "package.json",
    "tsconfig.json",
    ".mocharc.json",
    ".mocharc.js",
    ".mocharc.yml",
    ".coveragerc",
    "Makefile",
}
_CONFIG_PATTERNS = (
    re.compile(r"^(jest|vitest|vite|mocha|ava|playwright)\.config\.[cm]?[jt]s$"),
    re.compile(r"^.*\.pth$"),
)
_SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".mts", ".cts", ".js", ".mjs", ".cjs", ".jsx"}


def is_ci_file(path: str) -> bool:
    p = PurePosixPath(path)
    return (
        (len(p.parts) >= 2 and p.parts[0] == ".github" and p.parts[1] == "workflows")
        or p.name in {".gitlab-ci.yml", ".travis.yml", "azure-pipelines.yml", "Jenkinsfile"}
        or (len(p.parts) >= 1 and p.parts[0] == ".circleci")
    )


def is_test_config(path: str) -> bool:
    p = PurePosixPath(path)
    return p.name in _CONFIG_NAMES or any(r.match(p.name) for r in _CONFIG_PATTERNS) or is_ci_file(path)


def is_test_path(path: str) -> bool:
    """Test code, snapshots and anything living under a test directory."""
    p = PurePosixPath(path)
    if any(part in _TEST_DIRS for part in p.parts[:-1]):
        return True
    name = p.name
    return bool(_PY_TEST_NAME.match(name) or _TS_TEST_NAME.match(name) or _SNAPSHOT_NAME.match(name))


def classify(path: str, fixture_paths: frozenset[str] = frozenset()) -> str:
    """Classify one repository-relative POSIX path.

    `fixture_paths` are files outside test directories that visible tests read (see `fixture_paths_from_tests`).
    `conftest.py` counts as a test file; the config detector also inspects it.
    """
    if is_test_path(path) or path in fixture_paths:
        return TEST
    if is_test_config(path):
        return TEST_CONFIG
    if PurePosixPath(path).suffix in _SOURCE_SUFFIXES:
        return SOURCE
    return OTHER


_STRING_LITERAL = re.compile(r"""(?:'([^'\n]{1,200})'|"([^"\n]{1,200})"|`([^`\n]{1,200})`)""")


def fixture_paths_from_tests(test_sources: dict[str, str], repo_files: list[str]) -> frozenset[str]:
    """Non-test repository files that a visible test names in a string literal (data files the tests read)."""
    literals: set[str] = set()
    for text in test_sources.values():
        for m in _STRING_LITERAL.finditer(text):
            lit = next(g for g in m.groups() if g is not None)
            literals.add(lit.lstrip("./"))
    found = set()
    for f in repo_files:
        if is_test_path(f) or PurePosixPath(f).suffix in _SOURCE_SUFFIXES or is_test_config(f):
            continue
        name = PurePosixPath(f).name
        if f in literals or any(lit.endswith("/" + name) or lit == name for lit in literals):
            found.add(f)
    return frozenset(found)
