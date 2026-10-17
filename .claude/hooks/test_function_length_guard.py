"""Tests for function_length_guard: a function body stays within the limit."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import function_length_guard  # noqa: E402
from function_length_guard import find_violations  # noqa: E402

HOOKS_DIR = Path(__file__).parent
DOCSTRING = '    """Return the total."""\n\n    # Start from nothing.\n'


def _python(name: str, lines: int, heading: str = "") -> str:
    steps = "".join(f"    total += {step}\n" for step in range(lines - 2))
    return f"def {name}():\n{heading}    total = 0\n{steps}    return total\n"


def _blocked_reasons(capsys: pytest.CaptureFixture, check, *arguments) -> str:
    with pytest.raises(SystemExit) as blocked:
        check(*arguments)
    assert blocked.value.code == 2
    return capsys.readouterr().err


def test_find_violations_at_the_limit_returns_nothing():
    assert find_violations(_python("apply_discount", 20), "orders.py") == []


def test_find_violations_one_line_over_the_limit_reports_the_function():
    assert find_violations(_python("apply_discount", 21), "orders.py") == [
        "apply_discount: body is 21 lines; the limit is 20"
    ]


def test_check_write_with_long_function_exits_2(capsys: pytest.CaptureFixture):
    reasons = _blocked_reasons(
        capsys, function_length_guard.check_write, "orders.py",
        _python("apply_discount", 21),
    )
    assert "apply_discount: body is 21 lines; the limit is 20" in reasons
    assert "code-style.md" in reasons


@pytest.mark.parametrize(
    "file_name, lines", [("orders.py", 20), ("src/test_orders.py", 30)]
)
def test_check_write_within_limit_or_in_test_file_does_not_block(
    file_name: str, lines: int
):
    code = _python("apply_discount", lines)
    assert function_length_guard.check_write(file_name, code) is None


def test_check_write_with_guard_disabled_does_not_block(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("FUNCTION_LENGTH_GUARD_DISABLE", "1")
    code = _python("apply_discount", 21)
    assert function_length_guard.check_write("orders.py", code) is None


def test_check_edit_adding_long_function_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    target = tmp_path / "orders.py"
    target.write_text(_python("apply_fee", 5))
    added = _python("apply_fee", 5) + "\n\n" + _python("apply_discount", 21)
    reasons = _blocked_reasons(
        capsys, function_length_guard.check_edit, str(target),
        _python("apply_fee", 5), added,
    )
    assert "apply_discount: body is 21 lines" in reasons


@pytest.mark.parametrize(
    "old_line, new_line",
    [
        ("    total += 3\n", "    total += 300\n"),
        ("    total += 3\n", ""),
    ],
)
def test_check_edit_keeping_or_shortening_long_function_does_not_block(
    tmp_path: Path, old_line: str, new_line: str
):
    target = tmp_path / "orders.py"
    target.write_text(_python("apply_discount", 30))
    edited = function_length_guard.check_edit(str(target), old_line, new_line)
    assert edited is None


def test_check_edit_lengthening_long_function_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    target = tmp_path / "orders.py"
    target.write_text(_python("apply_discount", 30))
    reasons = _blocked_reasons(
        capsys, function_length_guard.check_edit, str(target),
        "    total += 3\n", "    total += 3\n    total += 300\n",
    )
    assert "apply_discount: body is 31 lines; the limit is 20" in reasons


def test_check_edit_of_file_that_does_not_exist_does_not_block(tmp_path: Path):
    target = tmp_path / "orders.py"
    code = _python("apply_discount", 21)
    assert function_length_guard.check_edit(str(target), "", code) is None


def test_find_violations_in_every_hook_module_returns_nothing():
    modules = [
        path for path in sorted(HOOKS_DIR.glob("*.py"))
        if not path.name.startswith("test_")
    ]
    found = {
        path.name: find_violations(path.read_text(), path.name) for path in modules
    }
    assert {name: listed for name, listed in found.items() if listed} == {}


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


def test_pre_write_with_long_function_exits_2():
    probe = HOOKS_DIR / "function_length_probe.py"
    content = _python("apply_discount", 21, DOCSTRING)
    result = _run_hook("pre-write.py", {"file_path": str(probe), "content": content})
    assert result.returncode == 2, result.stderr
    assert "apply_discount: body is 21 lines" in result.stderr


def test_pre_edit_lengthening_function_past_limit_exits_2(tmp_path: Path):
    target = tmp_path / "orders.py"
    target.write_text(_python("apply_discount", 20, DOCSTRING))
    tool_input = {
        "file_path": str(target),
        "old_string": "    total += 3\n",
        "new_string": "    total += 3\n    total += 300\n",
    }
    result = _run_hook("pre-edit.py", tool_input)
    assert result.returncode == 2, result.stderr
    assert "apply_discount: body is 21 lines" in result.stderr
