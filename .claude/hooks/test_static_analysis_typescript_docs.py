"""Tests for static-analysis.sh: exported TypeScript without a fitting JSDoc fails lint.

ESLint with eslint-plugin-jsdoc runs with the kit's
lint-config/eslint-jsdoc.config.mjs. Both are installed into LINT_NODE_PREFIX,
lint-config/ by default, because the config loads the plugin from there.
"""
import subprocess
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).parent
SCRIPT = HOOKS_DIR / "static-analysis.sh"
INSTALLER = HOOKS_DIR / "install-tool.sh"
CONFIG = HOOKS_DIR / "lint-config" / "eslint-jsdoc.config.mjs"
PACKAGES = "eslint@9 eslint-plugin-jsdoc typescript-eslint"
UNDOCUMENTED = "export function refund(total: number): number {\n  return total;\n}\n"
DOCUMENTED = (
    "/**\n * Refunds an order.\n * @param total - the amount paid.\n"
    " * @returns the amount paid back.\n */\n" + UNDOCUMENTED
)


def _prefix_with_eslint(tmp_path: Path, tool_stubs) -> Path:
    prefix = tmp_path / "node"
    tool_stubs.add("eslint")
    (prefix / "node_modules" / ".bin").mkdir(parents=True)
    (prefix / "node_modules" / "eslint-plugin-jsdoc").mkdir()
    (tool_stubs.commands / "eslint").rename(prefix / "node_modules" / ".bin" / "eslint")
    return prefix


def test_install_tool_with_eslint_jsdoc_missing_installs_it_into_the_prefix(
    tmp_path: Path, tool_stubs
):
    tool_stubs.add("npm")
    prefix = tmp_path / "node"
    tool_stubs.run_script(INSTALLER, "eslint-jsdoc", LINT_NODE_PREFIX=str(prefix))
    assert tool_stubs.calls() == [f"npm install --prefix {prefix} --no-save {PACKAGES}"]


def test_static_analysis_with_typescript_file_runs_the_jsdoc_rules(
    tmp_path: Path, tool_stubs
):
    prefix = _prefix_with_eslint(tmp_path, tool_stubs)
    source = tmp_path / "orders.ts"
    source.write_text(DOCUMENTED)
    for name in ["tsc", "biome"]:
        tool_stubs.add(name)
    result = tool_stubs.run_script(SCRIPT, str(source), LINT_NODE_PREFIX=str(prefix))
    assert result.returncode == 0, result.stderr
    moved_calls = (prefix / "node_modules" / "calls.log").read_text().splitlines()
    assert moved_calls == [f"eslint --config {CONFIG} --no-warn-ignored {source}"]


@pytest.mark.parametrize("code, rule", [
    (UNDOCUMENTED, "jsdoc/require-jsdoc"),
    (
        "/**\n * Refunds an order.\n * @returns the amount paid back.\n */\n" + UNDOCUMENTED,
        "jsdoc/require-param",
    ),
    (
        "/**\n * Refunds an order.\n * @param total - the amount paid.\n */\n" + UNDOCUMENTED,
        "jsdoc/require-returns",
    ),
])
def test_static_analysis_with_typescript_doc_comment_gap_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, code: str, rule: str
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "orders.ts").write_text(code)
    result = subprocess.run([str(SCRIPT), "orders.ts"], capture_output=True, text=True)
    assert result.returncode == 1
    assert rule in result.stdout


def test_static_analysis_with_documented_typescript_reports_no_jsdoc_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "orders.ts").write_text(DOCUMENTED)
    result = subprocess.run([str(SCRIPT), "orders.ts"], capture_output=True, text=True)
    assert "jsdoc/" not in result.stdout
