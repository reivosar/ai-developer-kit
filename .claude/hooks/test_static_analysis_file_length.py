"""Tests for static-analysis.sh: a code file longer than 200 lines is a finding."""
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent / "static-analysis.sh"
STATEMENT = "VALUE = 1\n"
PYLINT_FILE_LENGTH = (
    "pylint --disable=all --enable=too-many-lines --max-module-lines=200 --score=n"
)


def _module(directory: Path, line_count: int) -> Path:
    module = directory / "orders.py"
    module.write_text(STATEMENT * line_count)
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
    tool_stubs.add("pylint")
    result = tool_stubs.run_script(SCRIPT, str(module))
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [f"flake8 {module}", f"{PYLINT_FILE_LENGTH} {module}"]


def test_static_analysis_with_pylint_missing_installs_it(tmp_path: Path, tool_stubs):
    module = _module(tmp_path, 1)
    tool_stubs.add("flake8")
    tool_stubs.add("pipx", provides={"install pylint": ["pylint"]})
    result = tool_stubs.run_script(SCRIPT, str(module))
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [
        f"flake8 {module}", "pipx install pylint", f"{PYLINT_FILE_LENGTH} {module}"
    ]


def test_static_analysis_with_go_file_over_limit_exits_1(tmp_path: Path, tool_stubs):
    source = tmp_path / "orders.go"
    source.write_text("package orders\n")
    tool_stubs.add("go")
    tool_stubs.add("gofmt")
    tool_stubs.add("revive", status=1)
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 1
