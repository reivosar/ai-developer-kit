#!/usr/bin/env python3
"""
Allow-list check for Bash commands.
Exit 0 = allowed, Exit 2 = blocked.
"""
import sys
import json
import fnmatch
import os
import re
import subprocess
from pathlib import Path


def read_command():
    try:
        data = json.load(sys.stdin)
        return data.get("tool_input", {}).get("command", "")
    except Exception:
        return None


def load_patterns(settings_path, key):
    with open(settings_path) as f:
        settings = json.load(f)
    entries = settings.get("permissions", {}).get(key, [])
    return [e[5:-1] for e in entries if e.startswith("Bash(") and e.endswith(")")]


def split_segments(command: str) -> list[str]:
    """Split on &&, ;, and | that are outside of single or double quotes."""
    segments: list[str] = []
    current: list[str] = []
    in_single = in_double = False
    i = 0
    while i < len(command):
        c = command[i]
        if c == "'" and not in_double:
            in_single = not in_single
            current.append(c)
        elif c == '"' and not in_single:
            in_double = not in_double
            current.append(c)
        elif not in_single and not in_double:
            if command[i : i + 2] == "&&":
                seg = "".join(current).strip()
                if seg:
                    segments.append(seg)
                current = []
                i += 2
                continue
            elif c in (";", "|"):
                seg = "".join(current).strip()
                if seg:
                    segments.append(seg)
                current = []
                i += 1
                continue
            else:
                current.append(c)
        else:
            current.append(c)
        i += 1
    seg = "".join(current).strip()
    if seg:
        segments.append(seg)
    return segments if segments else [command]


def is_denied(command: str, patterns: list[str]) -> bool:
    candidates = [command] + split_segments(command)
    return any(fnmatch.fnmatch(c, p) for c in candidates for p in patterns)


def is_whitelisted(command: str, patterns: list[str]) -> bool:
    segments = split_segments(command)
    return all(any(fnmatch.fnmatch(seg, p) for p in patterns) for seg in segments)


def block(reason, cmd=None):
    msg = f"BLOCKED: {reason}"
    if cmd:
        msg += f"\n  Command: {cmd[:300]}"
    print(msg, file=sys.stderr)
    sys.exit(2)


def check_raw_operators(command: str) -> None:
    """Block any command containing '>' or '|' outside of quotes.

    Runs before the allow list so operator-injection like
    'echo evil > file' or 'cat file | bad_cmd' is caught immediately.
    """
    in_single = in_double = False
    for ch in command:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double:
            if ch == '>':
                block("shell redirect operator '>' is not permitted. "
                      "Use explicit file-writing tools instead.", command)
            elif ch == '|':
                block("pipe operator '|' is not permitted. "
                      "Run each command separately.", command)


def check_stash_destructive(command):
    if any(re.match(r"git\s+stash\s+(drop|clear)", seg.strip()) for seg in split_segments(command)):
        block("'git stash drop/clear' permanently deletes stashed work. "
              "Run 'git stash list' to review stashes before dropping.", command)


def check_checkout_discard(command):
    if any(re.match(r"git\s+checkout\s+--", seg.strip()) for seg in split_segments(command)):
        block("'git checkout --' discards uncommitted changes permanently. "
              "Use 'git diff' to review changes first, or 'git stash' to save them.", command)


def check_branch_force_delete(command):
    if any(re.match(r"git\s+branch\s+-D\b", seg.strip()) for seg in split_segments(command)):
        block("'git branch -D' force-deletes a branch. "
              "Use 'git branch -d' (safe delete) — it refuses to delete unmerged branches.", command)


def check_redirect_overwrite(command):
    match = re.search(r"(?<![>2])\s>(?![>&])\s*(\S+)", command)
    if match:
        target = os.path.expanduser(match.group(1))
        if os.path.exists(target):
            block(f"shell redirect '>' would overwrite existing file '{target}'. "
                  f"Use '>>' to append, or remove the file first if overwriting is intended.",
                  command)


def check_commit_on_main(command):
    if not any(re.match(r"git\s+commit\b", seg.strip())
               for seg in split_segments(command)):
        return
    branch = os.environ.get("MOCK_BRANCH")
    if branch is None:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True
        )
        branch = result.stdout.strip()
    if branch == "main":
        block("Cannot commit directly to main. "
              "Run: git checkout main && git pull "
              "&& git checkout -b <type>/<description>",
              command)


def check_cp_destination(command):
    """For recursive cp, move an existing destination directory to trash before copying."""
    import shlex
    for seg in split_segments(command):
        seg = seg.strip()
        if not re.match(r'cp\s', seg):
            continue
        try:
            args = shlex.split(seg)
        except ValueError:
            continue
        has_recursive = any(
            re.match(r'^-[a-zA-Z]*[rRa][a-zA-Z]*$', a)
            for a in args[1:]
            if a.startswith('-') and not a.startswith('--')
        )
        if not has_recursive:
            continue
        positional = [a for a in args[1:] if not a.startswith('-')]
        if len(positional) < 2:
            continue
        dst = positional[-1].rstrip('/')
        if not dst or dst in ('.', '..'):
            continue
        dst_path = os.path.expanduser(dst)
        if os.path.exists(dst_path):
            trash_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trash.sh')
            result = subprocess.run(['bash', trash_script, dst_path], capture_output=True)
            if result.returncode != 0:
                block(f"could not trash existing destination '{dst_path}' before copy — "
                      f"{result.stderr.decode().strip()}", command)
            print(f"INFO: moved existing '{dst_path}' to trash before copy", file=sys.stderr)


def check_cp_options(command: str) -> None:
    """Block cp invocations with force or target-directory options."""
    import shlex
    _BLOCKED = {'-t', '--target-directory', '-f', '--force'}
    for seg in split_segments(command):
        seg = seg.strip()
        if not re.match(r'cp\s', seg):
            continue
        try:
            args = shlex.split(seg)
        except ValueError:
            continue
        for arg in args[1:]:
            if arg in _BLOCKED:
                block(f"cp option '{arg}' is not permitted.", command)
            if arg.startswith('--target-directory='):
                block(f"cp option '{arg}' is not permitted.", command)


def check_python3_path(command: str) -> None:
    """Block python3 invocations referencing absolute paths or path traversal."""
    import shlex
    for seg in split_segments(command):
        seg = seg.strip()
        if not re.match(r'python3\s', seg):
            continue
        try:
            args = shlex.split(seg)
        except ValueError:
            continue
        for arg in args[1:]:
            if arg.startswith('-'):
                continue
            if arg.endswith('.py'):
                if arg.startswith('/'):
                    block(f"python3: absolute path '{arg}' is not permitted. "
                          "Use a relative path within the project.", command)
                if '../' in arg:
                    block(f"python3: path traversal '{arg}' is not permitted.", command)
                break


def run_blocklist_checks(command):
    check_stash_destructive(command)
    check_checkout_discard(command)
    check_branch_force_delete(command)
    check_redirect_overwrite(command)
    check_commit_on_main(command)
    check_cp_destination(command)
    check_cp_options(command)
    check_python3_path(command)


def main():
    settings_path = str(Path(__file__).resolve().parent.parent / 'settings.json')

    command = read_command()
    if not command:
        sys.exit(0)

    check_raw_operators(command)

    try:
        allow_patterns = load_patterns(settings_path, "allow")
        deny_patterns = load_patterns(settings_path, "deny")
    except Exception as e:
        print(f"BLOCKED: could not read settings.json — {e}", file=sys.stderr)
        sys.exit(2)

    if not is_whitelisted(command, allow_patterns):
        print(f"BLOCKED: command not in allow list: {command[:300]}", file=sys.stderr)
        sys.exit(2)

    if is_denied(command, deny_patterns):
        print(f"BLOCKED: command matches deny list: {command[:300]}", file=sys.stderr)
        sys.exit(2)

    run_blocklist_checks(command)
    sys.exit(0)


if __name__ == "__main__":
    main()
