"""Records the hooks keep: one directory per session under .claude/logs."""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

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
    # hook_lib imports this module, so the project root is read when needed.
    import hook_lib

    named = os.environ.get(RECORDS_DIR_VARIABLE)
    return Path(named) if named else hook_lib.REPO_ROOT / ".claude" / "logs"


def remember_session(hook_input: dict) -> None:
    """Keep the session of a hook input, so its records share one directory.

    The session's name is the first eight letters and digits of session_id.
    An input with no session_id puts the records under NO_SESSION.
    """
    global _session_name
    session_id = str(hook_input.get("session_id") or "")
    letters_and_digits = re.sub(r"[^A-Za-z0-9]", "", session_id)
    _session_name = letters_and_digits[:SESSION_NAME_LENGTH] or NO_SESSION


def utc_now() -> datetime:
    """Return the current time in UTC, the time every record carries."""
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
    return root / f"{utc_now().date().isoformat()}_{_session_name}"


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
