"""Tests for install-tool.sh: Checkstyle and detekt, the Java and Kotlin linters.

Each is one jar from its project's GitHub release, saved into LINT_JAR_DIR
(lint-config/jars by default) and run with the java already on the machine.
"""
from pathlib import Path

import pytest

INSTALLER = Path(__file__).parent / "install-tool.sh"
RELEASES = {
    "checkstyle": "https://github.com/checkstyle/checkstyle/releases/download/"
    "checkstyle-14.3.0/checkstyle-14.3.0-all.jar",
    "detekt": "https://github.com/detekt/detekt/releases/download/"
    "v1.23.8/detekt-cli-1.23.8-all.jar",
}


@pytest.mark.parametrize("tool", ["checkstyle", "detekt"])
def test_install_tool_with_jvm_linter_missing_downloads_its_jar(
    tmp_path: Path, tool_stubs, tool: str
):
    jars = tmp_path / "jars"
    tool_stubs.add("java")
    tool_stubs.add("curl")
    # The scripts see no command but stand-ins, so mkdir and mv are stand-ins too.
    tool_stubs.add("mkdir", silent=True)
    tool_stubs.add("mv", silent=True)
    tool_stubs.run_script(INSTALLER, tool, LINT_JAR_DIR=str(jars))
    assert tool_stubs.calls() == [
        f"curl -fsSL --retry 2 -o {jars}/{tool}.jar.part {RELEASES[tool]}"
    ]


@pytest.mark.parametrize("tool", ["checkstyle", "detekt"])
def test_install_tool_with_jvm_linter_jar_present_installs_nothing(
    tmp_path: Path, tool_stubs, tool: str
):
    jars = tmp_path / "jars"
    jars.mkdir()
    (jars / f"{tool}.jar").write_text("jar")
    tool_stubs.add("curl")
    result = tool_stubs.run_script(INSTALLER, tool, LINT_JAR_DIR=str(jars))
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == []


def test_install_tool_for_jvm_linter_without_java_exits_1(tmp_path: Path, tool_stubs):
    tool_stubs.add("curl")
    result = tool_stubs.run_script(INSTALLER, "checkstyle", LINT_JAR_DIR=str(tmp_path))
    assert result.returncode == 1
    assert "needs a Java runtime" in result.stderr
    assert tool_stubs.calls() == []
