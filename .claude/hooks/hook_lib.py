"""Shared hook utilities for Python hooks."""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, NoReturn


def _git_rev_parse(hooks_dir: Path, option: str) -> str:
    command = ["git", "-C", str(hooks_dir), "rev-parse", option]
    output = subprocess.check_output(
        command, text=True, stderr=subprocess.DEVNULL
    )
    return output.strip()


def _find_repo_root() -> Path:
    hooks_dir = Path(__file__).resolve().parent
    try:
        git_common = Path(_git_rev_parse(hooks_dir, "--git-common-dir"))
        if git_common.is_absolute():
            return git_common.parent
        return Path(_git_rev_parse(hooks_dir, "--show-toplevel")).resolve()
    except (OSError, subprocess.CalledProcessError):
        # Outside a git repository, or without git, the project is the
        # directory that holds .claude/. Raising here would stop every hook
        # from loading, and the guards would be off for the whole project.
        return hooks_dir.parents[1]


REPO_ROOT: Path = _find_repo_root()
WORKTREES_DIR: Path = REPO_ROOT / ".claude" / "worktrees"
RECORDS_DIR_VARIABLE = "HOOK_RECORDS_DIR"
NO_SESSION = "no-session"
SESSION_NAME_LENGTH = 8
# One hook process checks one tool call, so its session is kept for the whole
# process: block() is called from every guard and none of them has the input.
_session_name = NO_SESSION


def records_dir() -> Path:
    """Return the directory that holds the records of every session.

    It is .claude/logs unless HOOK_RECORDS_DIR names another directory. The
    tests set the variable, so they stay out of the project's own records.
    """
    named = os.environ.get(RECORDS_DIR_VARIABLE)
    return Path(named) if named else REPO_ROOT / ".claude" / "logs"


def remember_session(hook_input: dict) -> None:
    """Keep the session of a hook input, so its records share one directory.

    The session's name is the first eight letters and digits of session_id.
    An input with no session_id puts the records under NO_SESSION.
    """
    global _session_name
    session_id = str(hook_input.get("session_id") or "")
    letters_and_digits = re.sub(r"[^A-Za-z0-9]", "", session_id)
    _session_name = letters_and_digits[:SESSION_NAME_LENGTH] or NO_SESSION


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def session_records_dir() -> Path:
    """Return the directory for the records of the remembered session.

    Its name is the UTC date of the session's first record and the session's
    name, as in 2026-10-13_5a429071. A session that runs past midnight keeps
    its directory. Records with no session go under the current date.
    """
    root = records_dir()
    started = sorted(root.glob(f"*_{_session_name}"))
    if started and _session_name != NO_SESSION:
        return started[0]
    return root / f"{_utc_now().date().isoformat()}_{_session_name}"


def _keep_out_of_git(directory: Path) -> None:
    ignore_file = directory / ".gitignore"
    if not ignore_file.exists():
        ignore_file.write_text("*\n")


def append_record(record_name: str, entry: dict) -> None:
    """Append entry as one JSON line to record_name in the session's directory.

    record_name is a path below that directory, such as "audit.jsonl" or
    "blocks/tdd_guard.jsonl". A record that cannot be written is dropped:
    recording must never change whether a tool call is blocked.
    """
    try:
        record_file = session_records_dir() / record_name
        record_file.parent.mkdir(parents=True, exist_ok=True)
        _keep_out_of_git(records_dir())
        with record_file.open("a") as records:
            records.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def read_text(file_path: str) -> str:
    """Return a file's text; undecodable bytes are replaced, not raised."""
    return Path(file_path).read_text(errors="replace")


def apply_edit(
    text: str, old_string: str, new_string: str, replace_all: bool
) -> str:
    """Return text as the Edit tool would leave it."""
    replacement_count = -1 if replace_all else 1
    return text.replace(old_string, new_string, replacement_count)


def read_stdin_json() -> dict:
    """Return the JSON object on stdin, or an empty dict when it is unreadable."""
    try:
        data = json.load(sys.stdin)
    except Exception:
        return {}
    if isinstance(data, dict):
        remember_session(data)
    return data


def read_hook_input() -> dict:
    """Return the hook's JSON input; raise ValueError when it is malformed.

    A blocking hook must not read unusable input as "nothing to check",
    so this raises where read_stdin_json returns an empty object.
    """
    try:
        data = json.load(sys.stdin)
    except ValueError as error:
        raise ValueError(f"hook input is not JSON: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("hook input is not a JSON object")
    remember_session(data)
    if not isinstance(data.get("tool_input", {}), dict):
        raise ValueError("tool_input is not a JSON object")
    return data


def run_fail_closed(main: Callable[[], None]) -> None:
    """Run a blocking hook; an unexpected error blocks the action."""
    try:
        main()
    except Exception as error:
        block(
            f"hook failed: {type(error).__name__}: {error}",
            "The action is blocked because the hook could not finish"
            " its checks.",
        )


def emit_additional_context(hook_event: str, notices: list[str]) -> None:
    """Print notices as non-blocking context that the agent reads."""
    if not notices:
        return
    context = {
        "hookEventName": hook_event,
        "additionalContext": "\n".join(notices),
    }
    print(json.dumps({"hookSpecificOutput": context}))


MAX_LINE = 300  # characters of one output line that a block message keeps


def tail_lines(text: str, count: int) -> list[str]:
    """Return the last count lines of text, each cut to MAX_LINE characters.

    Tool output can hold one line of many thousand characters, such as a
    linker command. Left whole, it buries the lines that say what failed.
    """
    return [line[:MAX_LINE] for line in text.strip().splitlines()[-count:]]


def block(reason: str, *detail_lines: str) -> NoReturn:
    """Record the block, print its reason and detail lines to stderr, exit with 2.

    The record goes to blocks/<guard>.jsonl in the session's directory. The
    guard is the file that called block, so one file counts one check.
    """
    guard = Path(sys._getframe(1).f_code.co_filename).stem
    append_record(f"blocks/{guard}.jsonl", {
        "timestamp": _utc_now().isoformat(),
        "guard": guard,
        "hook": Path(sys.argv[0]).name,
        "reason": reason,
        "details": list(detail_lines),
    })
    print(f"BLOCKED: {reason}", file=sys.stderr)
    for line in detail_lines:
        print(f"  {line}", file=sys.stderr)
    sys.exit(2)
