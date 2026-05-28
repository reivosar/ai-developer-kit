#!/usr/bin/env python3
"""Pre-commit quality checks (secrets, branch name, whitespace, .env, emoji)."""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

_COMMIT_RE = re.compile(r'(^|&&\s*|;\s*)git\s+commit\b')
_SECRET_RE = re.compile(
    r'(password|passwd|api_key|apikey|secret|token|private_key)'
    r'\s*[:=]\s*["\'][^"\']{4,}',
    re.IGNORECASE,
)
_BRANCH_PREFIX_RE = re.compile(r'^(feat|fix|docs|chore|refactor|test|perf)/')
_EMOJI_RE = re.compile(
    "[" + chr(0x1F300) + "-" + chr(0x1F9FF) + chr(0x2600) + "-" + chr(0x27BF) + chr(0xFE0F) + "]"
)


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True).stdout
    except Exception:
        return ""


def _is_commit(command: str) -> bool:
    return bool(_COMMIT_RE.search(command))


def _staged_files() -> list[str]:
    return [f for f in _run(["git", "diff", "--cached", "--name-only"]).splitlines() if f]


def _staged_diff() -> str:
    return _run(["git", "diff", "--cached", "-U0"])


def _check_secrets(diff: str) -> str | None:
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if _SECRET_RE.search(line[1:]) and ".example" not in line:
            return "Potential secret detected in staged changes. Remove it and use environment variables instead."
    return None


def _check_branch() -> str | None:
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    if branch in ("HEAD", "main", "master"):
        return None
    if not _BRANCH_PREFIX_RE.match(branch):
        return f"Branch name '{branch}' does not follow the required prefix pattern (feat/|fix/|docs/|chore/|refactor/|test/|perf/)."
    return None


def _check_whitespace() -> str | None:
    out = subprocess.run(
        ["git", "diff", "--cached", "--check"],
        capture_output=True, text=True,
    ).stdout
    if "trailing whitespace" in out:
        return "Trailing whitespace found. Run: git diff --cached --check"
    return None


def _check_env_files(staged: list[str]) -> str | None:
    for f in staged:
        base = os.path.basename(f)
        if (base == ".env" or base.startswith(".env.")) and base not in (".env.sample", ".env.example"):
            return f"'.env' files must not be committed ({f}). Use .env.sample or .env.example instead."
    return None


def _check_emoji(diff: str) -> str | None:
    added = "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    if _EMOJI_RE.search(added):
        return "Emoji detected in staged changes. Use plain text instead (e.g. 'Good:' / 'Bad:')."
    return None


def check_pre_commit(command: str) -> None:
    if not _is_commit(command):
        return
    staged = _staged_files()
    if not staged:
        return
    diff = _staged_diff()
    errors = []
    for fn in (_check_secrets(diff), _check_branch(), _check_whitespace(),
               _check_env_files(staged), _check_emoji(diff)):
        if fn:
            errors.append(fn)
    if errors:
        hook_lib.block("Pre-commit checks failed:", *[f"- {e}" for e in errors])
