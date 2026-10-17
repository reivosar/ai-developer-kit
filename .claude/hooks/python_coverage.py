#!/usr/bin/env python3
"""Measure a project's Python tests under pytest-cov, installing the tools first."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import block, tail_lines  # noqa: E402

TEST_TIMEOUT = 300  # seconds
INSTALL_TIMEOUT = 300  # seconds
OUTPUT_LINES = 15
INSTALLER = Path(__file__).with_name("install-tool.sh")
_TESTS_FAILED, _USAGE_ERROR, _NO_TESTS_COLLECTED = 1, 4, 5


def last_lines(text: str) -> list[str]:
    """Return the last OUTPUT_LINES lines of a tool's output for a block message."""
    return tail_lines(text, OUTPUT_LINES)


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


def _read_report(result: subprocess.CompletedProcess, report_path: str) -> dict:
    output = last_lines(result.stdout + result.stderr)
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
            *last_lines(result.stderr),
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


def measure() -> dict:
    """Run the project's tests under coverage and return the JSON report.

    pytest and pytest-cov are installed first when one is missing. Failing
    tests, or a run that cannot measure, block the commit.

    Returns:
        The coverage.py JSON report, as a dict.
    """
    with tempfile.TemporaryDirectory() as directory:
        report_path = os.path.join(directory, "coverage.json")
        try:
            result = _run_tests_with_tools(report_path)
        except (OSError, subprocess.SubprocessError) as error:
            block("Coverage could not be measured.", str(error))
        return _read_report(result, report_path)
