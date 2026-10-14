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

# Every hook module is measured. A test that starts a hook as its own process
# runs it with sys.executable, and coverage follows that process; the line
# that only runs a script directly is not counted.
COVERAGE_CONFIG = (
    "[run]\n"
    "patch = subprocess\n"
    "[report]\n"
    "exclude_also =\n"
    "    if __name__ == .__main__.:\n"
)


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
    config_file = report_file.with_name("coveragerc")
    config_file.write_text(COVERAGE_CONFIG)
    environment = {
        **os.environ,
        "COVERAGE_FILE": f"{report_file}.data",
        "COVERAGE_GUARD_DISABLE": "1",
    }
    command = [
        sys.executable, "-m", "pytest", *_pytest_suites(), "-q",
        "-p", "no:cacheprovider", f"--cov={HOOKS_DIR}", "--cov-branch",
        f"--cov-config={config_file}", f"--cov-report=json:{report_file}",
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, cwd=KIT_ROOT, env=environment
    )
    assert result.returncode == 0, result.stdout[-2000:]
    return json.loads(report_file.read_text())


def test_every_hook_module_meets_coverage_threshold(report: dict):
    assert uncovered_files(report, _report_paths(_hook_modules())) == {}
