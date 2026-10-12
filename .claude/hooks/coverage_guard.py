#!/usr/bin/env python3
"""Guard: block a commit whose staged code its tests do not cover."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from commit_guard import is_commit, staged_files  # noqa: E402
from hook_lib import block  # noqa: E402
from tdd_guard import is_test_file  # noqa: E402

THRESHOLD = 90  # percent, for branches and for lines
TEST_TIMEOUT = 300  # seconds
INSTALL_TIMEOUT = 300  # seconds
OUTPUT_LINES = 15
INSTALLER = Path(__file__).with_name("install-tool.sh")
_MEASURED_SUFFIXES = {".py"}
_TESTS_PASSED, _TESTS_FAILED, _USAGE_ERROR, _NO_TESTS_COLLECTED = 0, 1, 4, 5


def _is_measured(path: str) -> bool:
    # Files under .claude/ belong to the kit, which measures them in its
    # own test_coverage.py; a project commit is not held up by them.
    if ".claude" in Path(path).parts or is_test_file(path):
        return False
    return Path(path).suffix in _MEASURED_SUFFIXES and os.path.isfile(path)


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
    """
    files = report.get("files", {})
    percents = {
        path: _percent(files[path]["summary"]) if path in files else 0.0
        for path in paths
    }
    return {path: value for path, value in percents.items() if value < THRESHOLD}


def _run_tests(report_path: str) -> subprocess.CompletedProcess:
    environment = {
        **os.environ,
        "COVERAGE_FILE": report_path + ".data",
        # A test that runs this hook must not start a second measurement.
        "COVERAGE_GUARD_DISABLE": "1",
    }
    command = [
        "pytest", "-q", "-p", "no:cacheprovider", "--cov=.", "--cov-branch",
        f"--cov-report=json:{report_path}",
    ]
    return subprocess.run(
        command, capture_output=True, text=True, timeout=TEST_TIMEOUT,
        env=environment,
    )


def _last_lines(text: str) -> list[str]:
    return text.strip().splitlines()[-OUTPUT_LINES:]


def _read_report(result: subprocess.CompletedProcess, report_path: str) -> dict:
    output = _last_lines(result.stdout + result.stderr)
    if result.returncode == _TESTS_FAILED:
        block("Coverage was not measured because tests failed.", *output)
    if os.path.isfile(report_path):
        return json.loads(Path(report_path).read_text())
    if result.returncode == _NO_TESTS_COLLECTED:
        return {"files": {}}
    block("Coverage could not be measured.", *output)


def _lacks_coverage_plugin(result: subprocess.CompletedProcess) -> bool:
    return result.returncode == _USAGE_ERROR and "--cov" in result.stderr


def _install_test_tools() -> None:
    result = subprocess.run(
        [str(INSTALLER), "pytest", "pytest-cov"],
        capture_output=True, text=True, timeout=INSTALL_TIMEOUT,
    )
    if result.returncode != 0:
        block(
            "Coverage could not be measured: pytest and pytest-cov are not"
            " installed, and installing them failed.",
            *_last_lines(result.stderr),
        )


def _run_tests_after_install(report_path: str) -> subprocess.CompletedProcess:
    _install_test_tools()
    return _run_tests(report_path)


def _run_tests_with_tools(report_path: str) -> subprocess.CompletedProcess:
    """Run the tests, installing pytest or pytest-cov first when one is missing."""
    try:
        result = _run_tests(report_path)
    except FileNotFoundError:
        return _run_tests_after_install(report_path)
    if _lacks_coverage_plugin(result):
        return _run_tests_after_install(report_path)
    return result


def _measure() -> dict:
    with tempfile.TemporaryDirectory() as directory:
        report_path = os.path.join(directory, "coverage.json")
        try:
            result = _run_tests_with_tools(report_path)
        except (OSError, subprocess.SubprocessError) as error:
            block("Coverage could not be measured.", str(error))
        return _read_report(result, report_path)


def _block_uncovered(below: dict[str, float]) -> None:
    block(
        f"Staged code is below {THRESHOLD}% branch and line coverage.",
        *[f"{path}: {value:.0f}%" for path, value in sorted(below.items())],
        "Add tests for the uncovered branches. To list them, run:"
        " pytest --cov=. --cov-branch --cov-report=term-missing",
    )


def check_staged_coverage(command: str) -> None:
    """Block a git commit that stages code below the coverage threshold."""
    if os.environ.get("COVERAGE_GUARD_DISABLE") or not is_commit(command):
        return
    paths = [path for path in staged_files() if _is_measured(path)]
    if not paths:
        return
    below = uncovered_files(_measure(), paths)
    if below:
        _block_uncovered(below)
