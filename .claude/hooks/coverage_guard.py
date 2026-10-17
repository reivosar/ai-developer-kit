#!/usr/bin/env python3
"""Guard: block a commit whose staged code its tests do not cover."""
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, NamedTuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_runners  # noqa: E402
import python_coverage  # noqa: E402
from commit_guard import is_commit, staged_files  # noqa: E402
from hook_lib import block  # noqa: E402
from tdd_guard import is_test_file  # noqa: E402

THRESHOLD = 90  # percent, for branches and for lines
# The kit's own hooks are measured by this test, which fails when one of them
# is below THRESHOLD.
KIT_COVERAGE_TEST = Path(__file__).with_name("test_coverage.py")
KIT_HOOKS = (".claude", "hooks")
# TypeScript files that declare or configure and hold no logic to test.
_NO_LOGIC_ENDINGS = (".d.ts", ".config.ts", ".config.mts")


def _is_measured(path: str) -> bool:
    # Files under .claude/ belong to the kit, which measures them in its
    # own test_coverage.py; a project commit is not held up by them.
    if ".claude" in Path(path).parts or is_test_file(path):
        return False
    if path.endswith(_NO_LOGIC_ENDINGS):
        return False
    return path.endswith(_MEASURED_SUFFIXES) and os.path.isfile(path)


def _ratio(covered: int, total: int) -> float:
    return 100.0 * covered / total if total else 100.0


def _percent(summary: dict) -> float:
    branches = _ratio(
        summary.get("covered_branches", 0), summary.get("num_branches", 0)
    )
    lines = _ratio(
        summary.get("covered_lines", 0), summary.get("num_statements", 0)
    )
    return min(branches, lines)


def uncovered_files(report: dict, paths: list[str]) -> dict[str, float]:
    """Return each path below THRESHOLD with its coverage percent.

    The percent is the lower of branch and line coverage. A file that no
    test imported is absent from the report and counts as 0.

    Args:
        report: a coverage.py JSON report.
        paths: the files to look up, named as the report names them.
    """
    files = report.get("files", {})
    percents = {
        path: _percent(files[path]["summary"]) if path in files else 0.0
        for path in paths
    }
    return {path: value for path, value in percents.items() if value < THRESHOLD}


def _python_percents() -> dict[str, float]:
    files = python_coverage.measure().get("files", {})
    return {path: _percent(entry["summary"]) for path, entry in files.items()}


class _Language(NamedTuple):
    suffixes: tuple
    percents: Callable[[], dict[str, float]]  # runs the tests; percent per file
    listing: str  # the command that shows what is not covered


# Each runner is looked up when it is called, so a test can replace it.
_LANGUAGES = (
    _Language(
        (".py",), lambda: _python_percents(),
        "pytest --cov=. --cov-branch --cov-report=term-missing",
    ),
    _Language(
        (".go",), lambda: coverage_runners.go_percents(), "go test ./... -cover"
    ),
    _Language((".rs",), lambda: coverage_runners.rust_percents(), "cargo llvm-cov"),
    _Language(
        (".ts", ".tsx", ".mts"), lambda: coverage_runners.typescript_percents(),
        "npx vitest run --coverage, or npx jest --coverage",
    ),
)
_MEASURED_SUFFIXES = tuple(
    suffix for language in _LANGUAGES for suffix in language.suffixes
)


def _below_threshold(language: _Language, staged: list[str]) -> dict[str, float]:
    paths = [path for path in staged if path.endswith(language.suffixes)]
    if not paths:
        return {}
    percents = language.percents()
    # A file that no test reached is absent from the report and counts as 0.
    found = {path: percents.get(path, 0.0) for path in paths}
    return {path: value for path, value in found.items() if value < THRESHOLD}


def _block_uncovered(below: dict[str, float], listings: list[str]) -> None:
    block(
        f"Staged code is below {THRESHOLD}% branch and line coverage.",
        *[f"{path}: {value:.0f}%" for path, value in sorted(below.items())],
        "Add tests for the uncovered lines and branches. To list them, run:",
        *listings,
    )


def _run_kit_coverage_test() -> subprocess.CompletedProcess:
    environment = {**os.environ, "COVERAGE_GUARD_DISABLE": "1"}
    command = ["pytest", "-q", "-p", "no:cacheprovider", str(KIT_COVERAGE_TEST)]
    return subprocess.run(
        command, capture_output=True, text=True,
        timeout=python_coverage.TEST_TIMEOUT, env=environment,
    )


def _stages_kit_hook(staged: list[str]) -> bool:
    return any(
        Path(path).parts[:2] == KIT_HOOKS and path.endswith(".py") for path in staged
    )


def _check_kit_coverage(staged: list[str]) -> None:
    if not _stages_kit_hook(staged) or not KIT_COVERAGE_TEST.is_file():
        return
    try:
        result = _run_kit_coverage_test()
    except (OSError, subprocess.SubprocessError) as error:
        block("The kit's hook coverage could not be measured.", str(error))
    if result.returncode != 0:
        block(
            f"The kit's hooks are below {THRESHOLD}% coverage, or a hook test fails.",
            *python_coverage.last_lines(result.stdout + result.stderr),
            f"Run: pytest {KIT_COVERAGE_TEST}",
        )


def check_staged_coverage(command: str) -> None:
    """Block a git commit that stages code below the coverage threshold.

    Python, Go, Rust, and TypeScript files are measured, each by its own
    test run. Test files, files under .claude/, and TypeScript declaration
    and configuration files are not. A staged Python file under
    .claude/hooks/ runs the kit's own coverage test instead.

    Args:
        command: the Bash command line.
    """
    if os.environ.get("COVERAGE_GUARD_DISABLE") or not is_commit(command):
        return
    all_staged = staged_files()
    _check_kit_coverage(all_staged)
    staged = [path for path in all_staged if _is_measured(path)]
    below: dict[str, float] = {}
    listings: list[str] = []
    for language in _LANGUAGES:
        short = _below_threshold(language, staged)
        below.update(short)
        listings += [language.listing] if short else []
    if below:
        _block_uncovered(below, listings)
