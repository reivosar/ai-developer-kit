"""Tests for static-analysis.sh: every file passed as an argument is linted."""
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent / "static-analysis.sh"
UNUSED_IMPORT = "import os\n"
CLEAN_MODULE = "VALUE = 1\n"


def _write(directory: Path, name: str, source: str) -> Path:
    module = directory / name
    module.write_text(source)
    return module


def _run(*files: Path) -> subprocess.CompletedProcess:
    command = [str(SCRIPT), *(str(file) for file in files)]
    return subprocess.run(command, capture_output=True, text=True)


def test_static_analysis_with_one_failing_file_exits_1(tmp_path: Path) -> None:
    failing = _write(tmp_path, "failing.py", UNUSED_IMPORT)
    result = _run(failing)
    assert result.returncode == 1, result.stdout


def test_static_analysis_with_failing_file_among_several_exits_1(
    tmp_path: Path,
) -> None:
    clean = _write(tmp_path, "clean.py", CLEAN_MODULE)
    failing = _write(tmp_path, "failing.py", UNUSED_IMPORT)
    result = _run(clean, failing)
    assert result.returncode == 1, result.stdout
    assert "F401" in result.stdout


def test_static_analysis_with_failing_file_name_containing_space_exits_1(
    tmp_path: Path,
) -> None:
    failing = _write(tmp_path, "failing module.py", UNUSED_IMPORT)
    result = _run(failing)
    assert result.returncode == 1, result.stdout


def test_static_analysis_with_several_clean_files_exits_0(
    tmp_path: Path,
) -> None:
    first = _write(tmp_path, "first.py", CLEAN_MODULE)
    second = _write(tmp_path, "second.py", CLEAN_MODULE)
    result = _run(first, second)
    assert result.returncode == 0, result.stdout
