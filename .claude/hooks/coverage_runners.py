#!/usr/bin/env python3
"""Measure coverage per file for Go, Rust, and TypeScript projects."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_lib import block, tail_lines  # noqa: E402

INSTALLER = Path(__file__).with_name("install-tool.sh")
TEST_TIMEOUT = 300  # seconds
INSTALL_TIMEOUT = 600  # seconds; cargo-llvm-cov is compiled when it is installed
OUTPUT_LINES = 15
_GO_BLOCK = re.compile(
    r"^(?P<block>(?P<file>[^:\n]+):[\d.,]+) (?P<statements>\d+) (?P<count>\d+)$",
    re.MULTILINE,
)
_SUMMARY_FLAGS = {
    "vitest": [
        "run", "--coverage", "--coverage.reporter=json-summary",
        "--coverage.reportsDirectory=",
    ],
    "jest": ["--coverage", "--coverageReporters=json-summary", "--coverageDirectory="],
}


def _last_lines(text: str) -> list[str]:
    return tail_lines(text, OUTPUT_LINES)


def _ensure_tool(tool: str) -> None:
    if shutil.which(tool):
        return
    result = subprocess.run(
        [str(INSTALLER), tool], capture_output=True, text=True,
        timeout=INSTALL_TIMEOUT,
    )
    if result.returncode != 0:
        block(
            f"Coverage could not be measured: {tool} is not installed, and"
            " installing it failed.",
            *_last_lines(result.stderr),
        )


def _run(command: list[str]) -> subprocess.CompletedProcess:
    # A test that runs the commit hook must not start a second measurement.
    environment = {**os.environ, "COVERAGE_GUARD_DISABLE": "1"}
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=TEST_TIMEOUT,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError) as error:
        block("Coverage could not be measured.", str(error))
    if result.returncode != 0:
        output = _last_lines(result.stdout + result.stderr)
        block("Coverage was not measured because tests failed.", *output)
    return result


def _ratio(covered: int, total: int) -> float:
    return 100.0 * covered / total if total else 100.0


def _relative(path: str) -> str:
    return os.path.relpath(os.path.realpath(path), os.path.realpath(os.getcwd()))


def _go_blocks(profile: str) -> dict[str, tuple[str, int, bool]]:
    # A block is listed once per test binary that loaded it; it is covered
    # when any of those runs reached it.
    blocks: dict[str, tuple[str, int, bool]] = {}
    for found in _GO_BLOCK.finditer(profile):
        reached = int(found["count"]) > 0
        seen = blocks.get(found["block"], ("", 0, False))[2]
        statements = int(found["statements"])
        blocks[found["block"]] = (found["file"], statements, reached or seen)
    return blocks


def go_profile_percents(profile: str, module: str) -> dict[str, float]:
    """Return the statement coverage percent of each file in a Go profile.

    The profile names files by import path; module is the module's import
    path, and the result names them relative to the module root.
    """
    totals: dict[str, list[int]] = {}
    for file, statements, reached in _go_blocks(profile).values():
        counts = totals.setdefault(os.path.relpath(file, module), [0, 0])
        counts[0] += statements
        counts[1] += statements if reached else 0
    return {file: _ratio(covered, total) for file, (total, covered) in totals.items()}


def go_percents() -> dict[str, float]:
    """Run the Go tests and return the statement coverage percent per file.

    Go measures statements, not branches. A failing test blocks the commit.
    """
    _ensure_tool("go")
    module = _run(["go", "list", "-m"]).stdout.strip()
    with tempfile.TemporaryDirectory() as directory:
        profile = Path(directory) / "cover.out"
        _run(["go", "test", "./...", f"-coverprofile={profile}"])
        if not profile.is_file():
            return {}
        return go_profile_percents(profile.read_text(), module)


def _rust_percent(summary: dict) -> float:
    # Branch coverage is measured only on a nightly toolchain; a kind with
    # a count of zero was not measured and is left out.
    measured = [
        summary[kind]["percent"] for kind in ("lines", "regions", "branches")
        if summary.get(kind, {}).get("count")
    ]
    return min(measured, default=100.0)


def rust_percents() -> dict[str, float]:
    """Run the Rust tests and return the coverage percent per file.

    The percent is the lower of line and region coverage from cargo llvm-cov,
    and of branch coverage when the toolchain measures it. A failing test
    blocks the commit.
    """
    _ensure_tool("cargo-llvm-cov")
    with tempfile.TemporaryDirectory() as directory:
        report = Path(directory) / "coverage.json"
        flags = ["--json", "--summary-only", f"--output-path={report}"]
        _run(["cargo", "llvm-cov", *flags])
        data = json.loads(report.read_text()).get("data", [])
    files = [file for entry in data for file in entry.get("files", [])]
    return {_relative(file["filename"]): _rust_percent(file["summary"]) for file in files}


def _typescript_runner() -> str:
    try:
        package = json.loads(Path("package.json").read_text())
    except (OSError, ValueError):
        package = {}
    listed = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    runners = [runner for runner in _SUMMARY_FLAGS if runner in listed]
    if not runners:
        block("Coverage could not be measured: package.json names neither vitest nor jest.")
    return runners[0]


def _summary_percent(entry: dict) -> float:
    # A file with nothing to count reports "Unknown", which leaves nothing uncovered.
    percents = [entry[kind]["pct"] for kind in ("lines", "branches")]
    return min(pct if isinstance(pct, (int, float)) else 100.0 for pct in percents)


def typescript_percents() -> dict[str, float]:
    """Run the TypeScript tests and return the coverage percent per file.

    The runner is vitest or jest, whichever package.json names, and the
    percent is the lower of line and branch coverage. A failing test blocks
    the commit, and so does a project with neither runner.
    """
    runner = _typescript_runner()
    with tempfile.TemporaryDirectory() as directory:
        *flags, directory_flag = _SUMMARY_FLAGS[runner]
        _run(["npx", "--no-install", runner, *flags, directory_flag + directory])
        summary = json.loads((Path(directory) / "coverage-summary.json").read_text())
    return {
        _relative(path): _summary_percent(entry)
        for path, entry in summary.items() if path != "total"
    }
