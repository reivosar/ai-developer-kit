"""Tests for static-analysis.sh: every file passed as an argument is linted."""
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "static-analysis.sh"
LINT_CONFIG = SCRIPT.parent / "lint-config"
UNUSED_IMPORT = "import os\n"
CLEAN_MODULE = '"""Values."""\n\nVALUE = 1\n'
YAML_DOCUMENT = "key: value\n"


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


def test_static_analysis_with_missing_linter_installs_it_and_lints(
    tmp_path: Path, tool_stubs
) -> None:
    document = _write(tmp_path, "settings.yaml", YAML_DOCUMENT)
    tool_stubs.add("pipx", provides={"install yamllint": ["yamllint"]})
    result = tool_stubs.run_script(SCRIPT, str(document))
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [
        "pipx install yamllint", f"yamllint {document}"
    ]


def test_static_analysis_with_go_file_runs_vet_and_format_check(
    tmp_path: Path, tool_stubs
) -> None:
    source = _write(tmp_path, "orders.go", "package orders\n")
    tool_stubs.add("go")
    tool_stubs.add("gofmt")
    tool_stubs.add("revive")
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [
        f"go vet {source}", f"gofmt -l {source}",
        f"revive -config {LINT_CONFIG}/revive.toml -set_exit_status {source}",
    ]


def test_static_analysis_with_unformatted_go_file_exits_1(
    tmp_path: Path, tool_stubs
) -> None:
    source = _write(tmp_path, "orders.go", "package orders\n")
    tool_stubs.add("go")
    tool_stubs.add("revive")
    tool_stubs.add("gofmt", output=str(source))
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 1
    assert f"gofmt: not formatted: {source}" in result.stdout


def test_static_analysis_with_typescript_file_runs_type_check_and_biome(
    tmp_path: Path, tool_stubs, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    source = _write(tmp_path, "order.ts", "export const total = 1;\n")
    tool_stubs.add("tsc")
    tool_stubs.add("biome")
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [
        f"tsc --noEmit {source}", f"biome lint --config-path {LINT_CONFIG} {source}"
    ]


def test_static_analysis_with_typescript_lint_finding_exits_1(
    tmp_path: Path, tool_stubs, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    source = _write(tmp_path, "order.ts", "var total = 1;\n")
    tool_stubs.add("tsc")
    tool_stubs.add("biome", status=1)
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 1


@pytest.mark.parametrize("config", ["eslint.config.mjs", ".eslintrc.json"])
def test_static_analysis_in_project_with_eslint_config_runs_eslint(
    tmp_path: Path, tool_stubs, monkeypatch, config: str
) -> None:
    monkeypatch.chdir(tmp_path)
    _write(tmp_path, config, "{}\n")
    source = _write(tmp_path, "order.tsx", "export const total = 1;\n")
    tool_stubs.add("tsc")
    tool_stubs.add("npx")
    tool_stubs.add("biome")
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [
        f"tsc --noEmit {source}",
        f"npx --no-install eslint --rule max-lines: [error, 200] {source}",
    ]


def test_static_analysis_with_linter_that_cannot_be_installed_exits_1(
    tmp_path: Path, tool_stubs
) -> None:
    document = _write(tmp_path, "settings.yaml", YAML_DOCUMENT)
    result = tool_stubs.run_script(SCRIPT, str(document))
    assert result.returncode == 1
    assert "yamllint is not installed and could not be installed" in result.stderr
    assert tool_stubs.calls() == []
