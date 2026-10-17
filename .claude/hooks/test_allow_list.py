"""Tests for the allow and deny lists: the matchers, and pre-bash.py per branch.

The commands pre-bash.py allows or blocks on a feature branch are listed in
test_allow_list_git.py, test_allow_list_git_options.py, and
test_allow_list_commands.py.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bash_guard  # noqa: E402
import cp_guard  # noqa: E402

SETTINGS = str(Path(__file__).parent.parent / "settings.json")
ALLOW = bash_guard.load_patterns(SETTINGS, "allow")
DENY = bash_guard.load_patterns(SETTINGS, "deny")


def _blocks(check, command: str) -> bool:
    try:
        check(command)
    except SystemExit:
        return True
    return False


@pytest.mark.parametrize("command, listed", [
    ("git status", True), ("git status --short", True), ("git status --porcelain", True),
    ("git switch main", True), ("git pull", True),
    ("python3 --version", True), ("node --version", False), ("rm -rf /", False),
])
def test_is_whitelisted_with_settings_allow_list_matches_listed_commands(
    command: str, listed: bool
):
    assert bash_guard.is_whitelisted(command, ALLOW) is listed


@pytest.mark.parametrize("command, denied", [
    ("git switch --detach HEAD", True), ("git switch main", False),
    ("git switch -c feat/foo", False), ("python3 --version", False),
    ("node --version", False), ("gh label create rule-gap --repo foo", True),
    ("gh label create bug --color e11d48", False),
])
def test_is_denied_with_settings_deny_list_matches_denied_commands(
    command: str, denied: bool
):
    assert bash_guard.is_denied(command, DENY) is denied


@pytest.mark.parametrize("command, segments", [
    ('python3 -c "import shutil; shutil.copytree(\'a\',\'b\')"',
     ['python3 -c "import shutil; shutil.copytree(\'a\',\'b\')"']),
    ("cd a && cd b", ["cd a", "cd b"]),
    ("echo 'a;b'", ["echo 'a;b'"]),
    ("git log | grep feat", ["git log", "grep feat"]),
    ("cat f | xargs cp -r", ["cat f", "xargs cp -r"]),
    ("echo 'a|b'", ["echo 'a|b'"]),
])
def test_split_segments_with_quoted_separator_keeps_it_in_the_segment(
    command: str, segments: list
):
    assert bash_guard.split_segments(command) == segments


@pytest.mark.parametrize("check, command, blocked", [
    (cp_guard.check_cp_destination, "git status", False),
    (cp_guard.check_cp_destination, "cp file.txt .", False),
    (cp_guard.check_cp_destination, "cp README.md docs/", False),
    (cp_guard.check_cp_destination, "cp src.txt .", False),
    (cp_guard.check_cp_source, "cp /tmp/foo.py .claude/hooks/bar.py", True),
    (cp_guard.check_cp_source, "cp /var/tmp/x.sh .claude/hooks/run.sh", True),
    (cp_guard.check_cp_source, "cp src/foo.py dst/bar.py", False),
    (cp_guard.check_cp_source, "cp .claude/hooks/a.py .claude/hooks/b.py", False),
    (cp_guard.check_cp_options, "cp --target-directory=dest/ src.txt", True),
    (cp_guard.check_cp_options, "cp -t dest/ src.txt", True),
    (cp_guard.check_cp_options, "cp -f src.txt dst.txt", True),
    (cp_guard.check_cp_options, "cp --force src.txt dst.txt", True),
    (cp_guard.check_cp_options, "cp src.txt dst.txt", False),
])
def test_cp_checks_with_listed_command_block_only_unsafe_copies(
    check, command: str, blocked: bool
):
    assert _blocks(check, command) is blocked


def test_parse_cp_segments_with_unclosed_quote_returns_without_raising():
    assert isinstance(list(cp_guard._parse_cp_segments("cp 'unclosed")), list)


@pytest.mark.parametrize("command, blocked", [
    ("git diff > patch.txt", True), ("cat f", False),
    ("echo 'a>b'", False), ('echo "a>b"', False), ("echo 'a'", False),
])
def test_check_raw_operators_with_unquoted_redirect_exits_2(
    command: str, blocked: bool
):
    assert _blocks(bash_guard.check_raw_operators, command) is blocked


@pytest.mark.parametrize("command, blocked", [
    ("python3 /tmp/evil.py", True), ("python3 ../attack.py", True),
    ("python3 tests/test_foo.py", False),
    ("python3 .claude/hooks/test_allow_list.py", False),
    ("python3 --version", False),
    ("pytest /tmp/test_evil.py", True), ("pytest ../test_attack.py", True),
    ("pytest .claude/worktrees/feat-foo/test_api.py", True),
    ("pytest tests/test_foo.py", False), ("pytest", False),
    ("pytest --cov=. --cov-branch", False),
    # Any script under .claude/worktrees/ is blocked whether or not it is listed.
    ("python3 .claude/worktrees/bootstrap/test_patch.py", True),
    ("python3 .claude/worktrees/feat-foo/test_api.py", True),
])
def test_check_python3_path_with_script_outside_project_exits_2(
    command: str, blocked: bool
):
    assert _blocks(bash_guard.check_python3_path, command) is blocked


def test_pre_bash_with_command_both_allowed_and_denied_blocks(pre_bash_blocks):
    assert pre_bash_blocks("git switch --detach HEAD")


@pytest.mark.parametrize("command, blocked, branch", [
    ("git commit -m 'test'", True, "main"),
    ("git commit -F /tmp/msg", True, "main"),
    ("git commit --amend", True, "main"),
    ("git commit -m 'test'", False, "feat/my-feature"),
    ("git commit -m 'test'", False, "fix/some-bug"),
    ("git status", False, "main"),
    ("git log --oneline", False, "main"),
    ("cd /repo && git commit -m 'test'", True, "main"),
    ("cd /repo && git commit -m 'test'", False, "feat/x"),
    ("git commit --amend", True, "feat/my-feature"),
    ("git commit --no-verify -m 'x'", True, "feat/my-feature"),
    ("git commit -a -m 'x'", True, "feat/my-feature"),
    ("git commit --all -m 'x'", True, "feat/my-feature"),
    ("git push origin HEAD", True, "main"),
    ("git push -u origin HEAD", True, "main"),
    ("git push origin HEAD", False, "feat/my-feature"),
    ("git merge origin/main", False, "main"),
    ("git pull --ff-only origin main", False, "main"),
])
def test_pre_bash_on_branch_blocks_commits_and_pushes_on_main(
    pre_bash_blocks, command: str, blocked: bool, branch: str
):
    assert pre_bash_blocks(command, branch) is blocked
