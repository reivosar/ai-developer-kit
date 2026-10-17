"""Tests for static-analysis.sh: Java and Kotlin doc comments and file length.

Java is linted by Checkstyle with lint-config/checkstyle-docs.xml, Kotlin by
detekt with lint-config/detekt-docs.yml. The real-tool tests need java; the
script downloads the jars when they are missing. The stand-in tests use the
empty jars that conftest.py's ToolStubs puts in its jar_dir.
"""
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "static-analysis.sh"
LINT_CONFIG = SCRIPT.parent / "lint-config"
JAVA_METHOD = "  public int refund(int total) {\n    return total;\n  }\n"
JAVA_DOCUMENTED = (
    "/** Orders. */\npublic class Orders {\n  /**\n   * Refunds an order.\n"
    "   * @param total the amount paid.\n   * @return the amount paid back.\n   */\n"
    + JAVA_METHOD + "}\n"
)
KOTLIN_DOCUMENTED = (
    "/** Orders. */\nclass Orders {\n    /**\n     * Refunds [total], the amount paid.\n"
    "     */\n    fun refund(total: Int): Int = total\n}\n"
)


def _run(source: Path) -> subprocess.CompletedProcess:
    return subprocess.run([str(SCRIPT), str(source)], capture_output=True, text=True)


def test_static_analysis_with_java_file_runs_checkstyle_with_kit_config(
    tmp_path: Path, tool_stubs
):
    source = tmp_path / "Orders.java"
    source.write_text(JAVA_DOCUMENTED)
    tool_stubs.add("java")
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 0, result.stderr
    jar = tool_stubs.jar_dir / "checkstyle.jar"
    assert tool_stubs.calls() == [
        f"java -Duser.language=en -jar {jar} -c {LINT_CONFIG}/checkstyle-docs.xml {source}"
    ]


def test_static_analysis_with_kotlin_files_runs_detekt_on_all_of_them(
    tmp_path: Path, tool_stubs
):
    first, second = tmp_path / "Orders.kt", tmp_path / "Refunds.kt"
    first.write_text(KOTLIN_DOCUMENTED)
    second.write_text(KOTLIN_DOCUMENTED)
    tool_stubs.add("java")
    result = tool_stubs.run_script(SCRIPT, str(first), str(second))
    assert result.returncode == 0, result.stderr
    jar = tool_stubs.jar_dir / "detekt.jar"
    assert tool_stubs.calls() == [
        f"java -jar {jar} --config {LINT_CONFIG}/detekt-docs.yml --input {first},{second}"
    ]


@pytest.mark.parametrize("code, rule", [
    ("public class Orders {\n" + JAVA_METHOD + "}\n", "MissingJavadocType"),
    ("/** Orders. */\npublic class Orders {\n" + JAVA_METHOD + "}\n", "MissingJavadocMethod"),
    (
        "/** Orders. */\npublic class Orders {\n  /**\n   * Refunds an order.\n"
        "   * @return the amount.\n   */\n" + JAVA_METHOD + "}\n",
        "JavadocMethod",
    ),
    ("/** Orders. */\npublic class Orders {\n" + "\n" * 200 + "}\n", "FileLength"),
])
def test_static_analysis_with_java_doc_or_length_gap_exits_1(
    tmp_path: Path, code: str, rule: str
):
    source = tmp_path / "Orders.java"
    source.write_text(code)
    result = _run(source)
    assert result.returncode == 1
    assert f"[{rule}]" in result.stdout


@pytest.mark.parametrize("name, code", [
    ("Orders.java", JAVA_DOCUMENTED), ("Orders.kt", KOTLIN_DOCUMENTED),
])
def test_static_analysis_with_documented_jvm_file_exits_0(
    tmp_path: Path, name: str, code: str
):
    source = tmp_path / name
    source.write_text(code)
    result = _run(source)
    assert result.returncode == 0, result.stdout + result.stderr


def test_static_analysis_with_undocumented_kotlin_function_exits_1(tmp_path: Path):
    source = tmp_path / "Orders.kt"
    source.write_text(
        "/** Orders. */\nclass Orders {\n    fun refund(total: Int): Int = total\n}\n"
    )
    result = _run(source)
    assert result.returncode == 1
    assert "UndocumentedPublicFunction" in result.stdout


def test_static_analysis_with_kotlin_file_over_200_lines_exits_1(tmp_path: Path):
    source = tmp_path / "Orders.kt"
    source.write_text(KOTLIN_DOCUMENTED + "\n" * 200)
    result = _run(source)
    assert result.returncode == 1
    assert "lines, more than 200" in result.stdout
