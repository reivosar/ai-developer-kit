"""Tests for doc_comment_guard's Write and Edit checks, also through the hooks."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doc_comment_guard  # noqa: E402

HOOKS_DIR = Path(__file__).parent
PY_DOCUMENTED = (
    "def apply_discount(total, rate):\n"
    '    """Return the total after the discount."""\n'
    "    return total - rate\n"
)
PY_UNDOCUMENTED = "def apply_fee(total, fee):\n    return total + fee\n"
PY_ARGS = '''
def apply_discount(total, rate):
    """Return the total after the discount.

    Args:
        total: The amount before the discount.
        rate: The discount.
    """
    return total - rate
'''


def _blocked_reasons(capsys: pytest.CaptureFixture, check, *arguments) -> str:
    with pytest.raises(SystemExit) as blocked:
        check(*arguments)
    assert blocked.value.code == 2
    return capsys.readouterr().err


def _edited(tmp_path: Path, content: str) -> Path:
    target = tmp_path / "orders.py"
    target.write_text(content)
    return target


def test_check_write_with_undocumented_function_exits_2(
    capsys: pytest.CaptureFixture,
):
    reasons = _blocked_reasons(
        capsys, doc_comment_guard.check_write, "orders.py", PY_UNDOCUMENTED
    )
    assert "apply_fee: no doc comment" in reasons
    assert "code-style.md" in reasons


@pytest.mark.parametrize("file_name", ["orders.py", "src/test_orders.py"])
def test_check_write_with_documented_or_test_file_does_not_block(file_name: str):
    code = PY_DOCUMENTED if file_name == "orders.py" else PY_UNDOCUMENTED
    assert doc_comment_guard.check_write(file_name, code) is None


def test_check_write_with_guard_disabled_does_not_block(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DOC_COMMENT_GUARD_DISABLE", "1")
    assert doc_comment_guard.check_write("orders.py", PY_UNDOCUMENTED) is None


@pytest.mark.parametrize(
    "existing, old, new",
    [
        (PY_DOCUMENTED, PY_DOCUMENTED, PY_DOCUMENTED + "\n\n" + PY_UNDOCUMENTED),
        (PY_UNDOCUMENTED, PY_UNDOCUMENTED, PY_UNDOCUMENTED + "\n\n" + PY_UNDOCUMENTED),
    ],
)
def test_check_edit_adding_undocumented_function_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture, existing: str, old: str, new: str
):
    target = _edited(tmp_path, existing)
    reasons = _blocked_reasons(capsys, doc_comment_guard.check_edit, str(target), old, new)
    assert "apply_fee: no doc comment" in reasons


def test_check_edit_changing_body_of_undocumented_function_does_not_block(
    tmp_path: Path,
):
    target = _edited(tmp_path, PY_UNDOCUMENTED)
    edited = doc_comment_guard.check_edit(
        str(target), "return total + fee", "return fee + total"
    )
    assert edited is None


def test_check_edit_renaming_documented_parameter_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    target = _edited(tmp_path, PY_ARGS)
    reasons = _blocked_reasons(
        capsys, doc_comment_guard.check_edit, str(target),
        "def apply_discount(total, rate):", "def apply_discount(total, percent):",
    )
    assert "omits 'percent'" in reasons


def test_check_edit_of_file_that_does_not_exist_does_not_block(tmp_path: Path):
    target = tmp_path / "orders.py"
    assert doc_comment_guard.check_edit(str(target), "", PY_UNDOCUMENTED) is None


def _run_hook(hook_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "WORKTREE_GUARD_DISABLE": "1",
        "ANOMALY_PATH_ESCAPE_DISABLE": "1",
        "TDD_GUARD_DISABLE": "1",
    }
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / hook_name)],
        input=json.dumps({"tool_input": tool_input}),
        capture_output=True, text=True, env=env,
    )


def test_pre_write_with_undocumented_function_exits_2():
    probe = HOOKS_DIR / "doc_comment_probe.py"
    tool_input = {"file_path": str(probe), "content": PY_UNDOCUMENTED}
    result = _run_hook("pre-write.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "apply_fee: no doc comment" in result.stderr


def test_pre_edit_adding_undocumented_function_exits_2(tmp_path: Path):
    target = _edited(tmp_path, PY_DOCUMENTED)
    tool_input = {
        "file_path": str(target),
        "old_string": PY_DOCUMENTED,
        "new_string": PY_DOCUMENTED + "\n\n" + PY_UNDOCUMENTED,
    }
    result = _run_hook("pre-edit.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "apply_fee: no doc comment" in result.stderr
