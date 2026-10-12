"""Coverage test: each hook module meets the kit's coverage threshold."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coverage_guard import uncovered_files  # noqa: E402

HOOKS_DIR = Path(__file__).parent
KIT_ROOT = HOOKS_DIR.parents[1]
PYTEST_TEST = re.compile(r"^\s*def test_", re.MULTILINE)
# A script-style suite ends its own process at module level, which aborts
# pytest's collection, so it cannot join the measured run.
SCRIPT_RUNNER = re.compile(r"^(?:sys\.exit\(|raise SystemExit)", re.MULTILINE)

# Reached only through a subprocess or a script-style suite, which the
# in-process measurement cannot see. Remove a name once its module has
# pytest tests that import it.
NOT_MEASURED = {
    "anomaly_guard.py",
    "bash_guard.py",
    "content_guard.py",
    "cp_guard.py",
    "env_file_guard.py",
    "mcp_guard.py",
    "post-tool.py",
    "pre-bash.py",
    "pre-edit.py",
    "pre-mcp.py",
    "pre-write.py",
    "prompt_injection_guard.py",
    "run-hook.py",
    "user-prompt-submit.py",
}


def _hook_modules() -> set[str]:
    modules = HOOKS_DIR.glob("*.py")
    return {path.name for path in modules if not path.name.startswith("test_")}


def _is_pytest_suite(path: Path) -> bool:
    if path.name == Path(__file__).name:
        return False
    source = path.read_text()
    return bool(PYTEST_TEST.search(source)) and not SCRIPT_RUNNER.search(source)


def _pytest_suites() -> list[str]:
    suites = sorted(HOOKS_DIR.glob("test_*.py"))
    return [str(path) for path in suites if _is_pytest_suite(path)]


def _report_paths(names: set[str]) -> list[str]:
    hooks_path = HOOKS_DIR.relative_to(KIT_ROOT)
    return [str(hooks_path / name) for name in sorted(names)]


@pytest.fixture(scope="module")
def report(tmp_path_factory: pytest.TempPathFactory) -> dict:
    report_file = tmp_path_factory.mktemp("coverage") / "coverage.json"
    environment = {
        **os.environ,
        "COVERAGE_FILE": f"{report_file}.data",
        "COVERAGE_GUARD_DISABLE": "1",
    }
    command = [
        sys.executable, "-m", "pytest", *_pytest_suites(), "-q",
        "-p", "no:cacheprovider", f"--cov={HOOKS_DIR}", "--cov-branch",
        f"--cov-report=json:{report_file}",
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, cwd=KIT_ROOT, env=environment
    )
    assert result.returncode == 0, result.stdout[-2000:]
    return json.loads(report_file.read_text())


def test_measured_hook_modules_meet_coverage_threshold(report: dict):
    measured = _hook_modules() - NOT_MEASURED
    assert uncovered_files(report, _report_paths(measured)) == {}


def test_not_measured_list_names_only_modules_below_threshold(report: dict):
    listed = _report_paths(NOT_MEASURED)
    assert sorted(uncovered_files(report, listed)) == listed


def test_not_measured_list_names_only_existing_modules():
    assert NOT_MEASURED - _hook_modules() == set()
