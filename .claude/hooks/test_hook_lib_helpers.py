"""Tests for the text and record helpers in hook_lib shared by the guards."""
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402


def test_tail_lines_returns_the_last_lines_in_order():
    assert hook_lib.tail_lines("first\nsecond\nthird\n", 2) == ["second", "third"]


def test_tail_lines_cuts_a_line_longer_than_the_limit():
    linker_command = "cc " + "-L/toolchain/lib " * 400
    lines = hook_lib.tail_lines(f"error: linking failed\n{linker_command}\n", 5)
    assert lines == ["error: linking failed", linker_command[:hook_lib.MAX_LINE]]


def test_apply_edit_with_repeated_text_replaces_first_occurrence_only():
    edited = hook_lib.apply_edit("a b a", "a", "c", replace_all=False)
    assert edited == "c b a"


def test_apply_edit_with_replace_all_replaces_every_occurrence():
    edited = hook_lib.apply_edit("a b a", "a", "c", replace_all=True)
    assert edited == "c b c"


def test_apply_edit_with_absent_text_returns_text_unchanged():
    assert hook_lib.apply_edit("a b a", "z", "c", replace_all=False) == "a b a"


def test_read_stdin_json_with_valid_object_returns_object(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"tool_name": "Bash"}'))
    assert hook_lib.read_stdin_json() == {"tool_name": "Bash"}


def test_read_stdin_json_with_unparsable_input_returns_empty_object(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert hook_lib.read_stdin_json() == {}


def test_find_repo_root_with_relative_git_directory_returns_toplevel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    git_outputs = iter([".git\n", f"{tmp_path}\n"])
    monkeypatch.setattr(
        hook_lib.subprocess, "check_output",
        lambda *arguments, **options: next(git_outputs),
    )
    assert hook_lib._find_repo_root() == tmp_path.resolve()


@pytest.mark.parametrize(
    "failure",
    [
        hook_lib.subprocess.CalledProcessError(128, ["git"]),
        FileNotFoundError("git"),
    ],
)
def test_find_repo_root_when_git_cannot_answer_returns_directory_holding_the_kit(
    monkeypatch: pytest.MonkeyPatch, failure: Exception
):
    def fail(*arguments: object, **options: object) -> str:
        raise failure

    monkeypatch.setattr(hook_lib.subprocess, "check_output", fail)
    hooks_directory = Path(hook_lib.__file__).resolve().parent
    assert hook_lib._find_repo_root() == hooks_directory.parents[1]


def test_read_text_with_utf8_file_returns_content(tmp_path: Path):
    document = tmp_path / "guide.md"
    document.write_text("first\nsecond\n")
    assert hook_lib.read_text(str(document)) == "first\nsecond\n"


def test_read_text_with_non_utf8_file_returns_text_without_raising(
    tmp_path: Path,
):
    document = tmp_path / "legacy.md"
    document.write_bytes(b"caf\xe9\n")
    assert hook_lib.read_text(str(document)).startswith("caf")


def _records(record_name: str) -> list[dict]:
    record_file = hook_lib.session_records_dir() / record_name
    return [json.loads(line) for line in record_file.read_text().splitlines()]


def _utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _occupy_records_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    occupied = tmp_path / "occupied"
    occupied.write_text("a file where the records directory should be")
    monkeypatch.setenv("HOOK_RECORDS_DIR", str(occupied))


def test_records_dir_without_override_returns_logs_under_the_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("HOOK_RECORDS_DIR")
    monkeypatch.setattr(hook_lib, "REPO_ROOT", tmp_path)
    assert hook_lib.records_dir() == tmp_path / ".claude" / "logs"


def test_records_dir_inside_a_test_returns_directory_outside_the_repository():
    # The fixture records_outside_the_project in conftest.py names the directory.
    assert hook_lib.REPO_ROOT not in hook_lib.records_dir().parents


def test_session_records_dir_with_session_is_named_by_date_and_session():
    hook_lib.remember_session({"session_id": "5a429071-2390-4847-942f"})
    directory = hook_lib.session_records_dir()
    assert directory == hook_lib.records_dir() / f"{_utc_today()}_5a429071"


def test_session_records_dir_with_directory_from_earlier_day_returns_it():
    hook_lib.remember_session({"session_id": "5a429071-2390-4847-942f"})
    started = hook_lib.records_dir() / "2026-10-01_5a429071"
    started.mkdir(parents=True)
    assert hook_lib.session_records_dir() == started


@pytest.mark.parametrize("hook_input", [{}, {"session_id": ""}, {"session_id": None}])
def test_session_records_dir_without_session_is_named_by_date_alone(
    hook_input: dict,
):
    hook_lib.remember_session(hook_input)
    (hook_lib.records_dir() / "2026-10-01_no-session").mkdir(parents=True)
    directory = hook_lib.session_records_dir()
    assert directory == hook_lib.records_dir() / f"{_utc_today()}_no-session"


def test_session_records_dir_with_path_in_session_id_stays_inside_records_dir():
    hook_lib.remember_session({"session_id": "../../etc/passwd"})
    directory = hook_lib.session_records_dir()
    assert directory == hook_lib.records_dir() / f"{_utc_today()}_etcpassw"


def test_read_hook_input_with_session_id_remembers_the_session(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"session_id": "9f8e7d6c-1"}'))
    hook_lib.read_hook_input()
    assert hook_lib.session_records_dir().name == f"{_utc_today()}_9f8e7d6c"


def test_read_stdin_json_with_session_id_remembers_the_session(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"session_id": "1a2b3c4d-9"}'))
    hook_lib.read_stdin_json()
    assert hook_lib.session_records_dir().name == f"{_utc_today()}_1a2b3c4d"


def test_read_stdin_json_with_list_input_keeps_the_remembered_session(
    monkeypatch: pytest.MonkeyPatch,
):
    hook_lib.remember_session({"session_id": "5a429071"})
    monkeypatch.setattr(sys, "stdin", io.StringIO("[1, 2]"))
    assert hook_lib.read_stdin_json() == [1, 2]
    assert hook_lib.session_records_dir().name == f"{_utc_today()}_5a429071"


def test_append_record_called_twice_writes_one_json_line_per_call():
    hook_lib.append_record("audit.jsonl", {"tool_name": "Bash"})
    hook_lib.append_record("audit.jsonl", {"tool_name": "Edit"})
    assert _records("audit.jsonl") == [{"tool_name": "Bash"}, {"tool_name": "Edit"}]


def test_append_record_with_new_directory_keeps_the_records_out_of_git():
    hook_lib.append_record("blocks/tdd_guard.jsonl", {"reason": "No test found."})
    assert (hook_lib.records_dir() / ".gitignore").read_text() == "*\n"


def test_append_record_with_unwritable_directory_does_not_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _occupy_records_dir(tmp_path, monkeypatch)
    written = hook_lib.append_record("blocks/tdd_guard.jsonl", {"reason": "No test."})
    assert written is None


def test_block_with_reason_and_detail_records_the_calling_guard():
    with pytest.raises(SystemExit) as blocked:
        hook_lib.block("No test for 'orders.py' found.", "File: orders.py")
    assert blocked.value.code == 2
    [entry] = _records("blocks/test_hook_lib_helpers.jsonl")
    assert entry["guard"] == "test_hook_lib_helpers"
    assert entry["reason"] == "No test for 'orders.py' found."
    assert entry["details"] == ["File: orders.py"]
    assert datetime.fromisoformat(entry["timestamp"]).tzinfo is not None


def test_block_with_unwritable_records_still_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    _occupy_records_dir(tmp_path, monkeypatch)
    with pytest.raises(SystemExit) as blocked:
        hook_lib.block("No test found.")
    assert blocked.value.code == 2
    assert "BLOCKED: No test found." in capsys.readouterr().err


def test_run_fail_closed_with_raising_hook_records_the_failure_under_hook_lib():
    def raise_from_guard() -> None:
        raise RuntimeError("guard broke")

    with pytest.raises(SystemExit) as blocked:
        hook_lib.run_fail_closed(raise_from_guard)
    assert blocked.value.code == 2
    [entry] = _records("blocks/hook_lib.jsonl")
    assert entry["reason"] == "hook failed: RuntimeError: guard broke"
