"""Tests for static-analysis.sh: shell functions carry Google style header comments.

The Google Shell Style Guide asks each function for a header comment that
describes it and lists, as they apply, its Arguments, Outputs, and Returns.
shell-docs.sh checks the header is there and names each part the body uses.
"""
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "static-analysis.sh"
HEADER = "#######################################\n# Cancel an order.\n"
END = "#######################################\n"


def _script(directory: Path, text: str) -> Path:
    script = directory / "orders.sh"
    script.write_text("#!/usr/bin/env bash\n\n" + text)
    return script


def _run(script: Path) -> subprocess.CompletedProcess:
    return subprocess.run([str(SCRIPT), str(script)], capture_output=True, text=True)


@pytest.mark.parametrize("text, problem", [
    ("cancel() {\n    true\n}\n", "cancel: no header comment"),
    (
        "# A comment for the file.\n\nfunction cancel {\n    true\n}\n",
        "cancel: no header comment",
    ),
    (
        HEADER + END + 'cancel() {\n    local order="$1"\n}\n',
        "cancel: header comment lists no Arguments:",
    ),
    (
        HEADER + END + 'cancel() {\n    shift\n    run "$@"\n}\n',
        "cancel: header comment lists no Arguments:",
    ),
    (
        HEADER + END + 'cancel() {\n    echo "cancelled"\n}\n',
        "cancel: header comment lists no Outputs:",
    ),
    (HEADER + END + "cancel() {\n    return 1\n}\n", "cancel: header comment lists no Returns:"),
])
def test_static_analysis_with_shell_function_header_gap_exits_1(
    tmp_path: Path, text: str, problem: str
):
    result = _run(_script(tmp_path, text))
    assert result.returncode == 1
    assert problem in result.stdout


@pytest.mark.parametrize("text", [
    HEADER + END + "cancel() {\n    true\n}\n",
    HEADER + "# Arguments:\n#   The order to cancel.\n# Outputs:\n#   The order, to stdout.\n"
    "# Returns:\n#   1 when the order is unknown.\n" + END
    + 'cancel() {\n    echo "$1"\n    return 1\n}\n',
    HEADER + END + "cancel() {\n    true\n}\n\n" + HEADER + END + "refund() {\n    true\n}\n",
    HEADER + END + 'cancel() {\n    ready || return\n    "$SHELL" -c true || exit_code=1\n}\n',
    HEADER + END + 'cancel() {\n    true\n}\n\necho "done"\nexit "$status"\n',
])
def test_static_analysis_with_documented_shell_functions_exits_0(tmp_path: Path, text: str):
    result = _run(_script(tmp_path, text))
    assert result.returncode == 0, result.stdout + result.stderr


def test_static_analysis_reads_each_function_body_up_to_the_next_function(tmp_path: Path):
    text = HEADER + END + "cancel() {\n    true\n}\n\nrefund() {\n    echo \"$1\"\n}\n"
    result = _run(_script(tmp_path, text))
    assert "cancel:" not in result.stdout
    assert "refund: no header comment" in result.stdout
