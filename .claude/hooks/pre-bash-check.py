#!/usr/bin/env python3
"""
Allow-list check for pre-bash.sh.
Exit 0 = allowed, Exit 2 = blocked.
"""
import sys
import json
import fnmatch
import os
import re
import subprocess


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
    """Split on && and ; that are outside of single or double quotes."""
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
            elif c == ";":
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


def block(reason):
    print(f"BLOCKED: {reason}", file=sys.stderr)
    sys.exit(2)


def check_stash_destructive(command):
    if any(re.match(r"git\s+stash\s+(drop|clear)", seg.strip()) for seg in split_segments(command)):
        block("'git stash drop/clear' permanently deletes stashed work. "
              "Run 'git stash list' to review stashes before dropping.")


def check_checkout_discard(command):
    if any(re.match(r"git\s+checkout\s+--", seg.strip()) for seg in split_segments(command)):
        block("'git checkout --' discards uncommitted changes permanently. "
              "Use 'git diff' to review changes first, or 'git stash' to save them.")


def check_branch_force_delete(command):
    if any(re.match(r"git\s+branch\s+-D\b", seg.strip()) for seg in split_segments(command)):
        block("'git branch -D' force-deletes a branch. "
              "Use 'git branch -d' (safe delete) — it refuses to delete unmerged branches.")


def check_redirect_overwrite(command):
    match = re.search(r"(?<![>2])\s>(?![>&])\s*(\S+)", command)
    if match:
        target = os.path.expanduser(match.group(1))
        if os.path.exists(target):
            block(f"shell redirect '>' would overwrite existing file '{target}'. "
                  f"Use '>>' to append, or remove the file first if overwriting is intended.")


def check_commit_on_main(command):
    if not re.match(r"git\s+commit\b", command.strip()):
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
              "&& git checkout -b <type>/<description>")


def run_blocklist_checks(command):
    check_stash_destructive(command)
    check_checkout_discard(command)
    check_branch_force_delete(command)
    check_redirect_overwrite(command)
    check_commit_on_main(command)


def main():
    settings_path = sys.argv[1]

    command = read_command()
    if not command:
        sys.exit(0)

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
