"""Tests for static-analysis.sh: a code file longer than 200 lines is a finding."""
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "static-analysis.sh"
STATEMENT = "VALUE = 1\n"
PYLINT_FILE_LENGTH = (
    "pylint --disable=all --enable=too-many-lines --max-module-lines=200 --score=n"
)


def _module(directory: Path, line_count: int) -> Path:
    module = directory / "orders.py"
    module.write_text('"""Orders."""\n' + STATEMENT * (line_count - 1))
    return module


def _run(*files: Path) -> subprocess.CompletedProcess:
    command = [str(SCRIPT), *(str(file) for file in files)]
    return subprocess.run(command, capture_output=True, text=True)


def test_static_analysis_with_python_file_over_200_lines_exits_1(tmp_path: Path):
    result = _run(_module(tmp_path, 201))
    assert result.returncode == 1, result.stdout
    assert "too-many-lines" in result.stdout


def test_static_analysis_with_python_file_of_200_lines_exits_0(tmp_path: Path):
    result = _run(_module(tmp_path, 200))
    assert result.returncode == 0, result.stdout + result.stderr


def test_static_analysis_with_python_file_runs_pylint_for_file_length(
    tmp_path: Path, tool_stubs
):
    module = _module(tmp_path, 1)
    tool_stubs.add("flake8")
    tool_stubs.add("ruff")
    tool_stubs.add("pylint")
    result = tool_stubs.run_script(SCRIPT, str(module))
    assert result.returncode == 0, result.stderr
    assert f"{PYLINT_FILE_LENGTH} {module}" in tool_stubs.calls()


def test_static_analysis_with_pylint_missing_installs_it(tmp_path: Path, tool_stubs):
    module = _module(tmp_path, 1)
    tool_stubs.add("flake8")
    tool_stubs.add("ruff")
    tool_stubs.add("pipx", provides={"install pylint": ["pylint"]})
    result = tool_stubs.run_script(SCRIPT, str(module))
    assert result.returncode == 0, result.stderr
    calls = tool_stubs.calls()
    assert calls[calls.index("pipx install pylint") + 1] == f"{PYLINT_FILE_LENGTH} {module}"


@pytest.mark.parametrize("name, line", [
    ("lib.rs", "pub fn total() {}\n"), ("deploy.sh", "echo done\n"),
    ("deploy.bash", "echo done\n"),
])
def test_static_analysis_with_file_no_linter_measures_over_200_lines_exits_1(
    tmp_path: Path, tool_stubs, name: str, line: str
):
    source = tmp_path / name
    source.write_text(line * 201)
    tool_stubs.add("cargo")
    tool_stubs.add("cargo-clippy")
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 1
    assert f"{source}: 201 lines, more than 200" in result.stdout


@pytest.mark.parametrize("name, text", [
    ("lib.rs", "pub fn total() {}\n" * 200), ("deploy.sh", "echo done\n" * 200),
    ("deploy.sh", "echo done\n" * 199 + "echo last"),
])
def test_static_analysis_with_file_no_linter_measures_within_200_lines_exits_0(
    tmp_path: Path, tool_stubs, name: str, text: str
):
    source = tmp_path / name
    source.write_text(text)
    tool_stubs.add("cargo")
    tool_stubs.add("cargo-clippy")
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 0, result.stdout + result.stderr


def test_static_analysis_with_go_file_over_limit_exits_1(tmp_path: Path, tool_stubs):
    source = tmp_path / "orders.go"
    source.write_text("package orders\n")
    tool_stubs.add("go")
    tool_stubs.add("gofmt")
    tool_stubs.add("revive", status=1)
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 1
