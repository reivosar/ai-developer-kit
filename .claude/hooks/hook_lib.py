"""Shared hook utilities for Python hooks."""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, NoReturn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_records  # noqa: E402


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


def add_tool_directory_to_path() -> None:
    """Add ~/.local/bin to PATH, where pipx and install-tool.sh put commands.

    A tool installed there by a commit check is then found by the command
    that runs next, even when the shell Claude Code started lacks the
    directory. Without HOME, PATH is left as it is.
    """
    home = os.environ.get("HOME")
    if not home:
        return
    tool_directory = os.path.join(home, ".local", "bin")
    directories = os.environ.get("PATH", "").split(os.pathsep)
    if tool_directory not in directories:
        listed = [directory for directory in directories if directory]
        os.environ["PATH"] = os.pathsep.join(listed + [tool_directory])


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
        hook_records.remember_session(data)
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
    hook_records.remember_session(data)
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
    hook_records.append_record(f"blocks/{guard}.jsonl", {
        "timestamp": hook_records.utc_now().isoformat(),
        "guard": guard,
        "hook": Path(sys.argv[0]).name,
        "reason": reason,
        "details": list(detail_lines),
    })
    print(f"BLOCKED: {reason}", file=sys.stderr)
    for line in detail_lines:
        print(f"  {line}", file=sys.stderr)
    sys.exit(2)
