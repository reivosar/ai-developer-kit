"""Tests for git_guard: options that force, delete, or discard, and unnamed subcommands."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import git_guard  # noqa: E402

ALLOW_PATTERNS = ["git diff*", "git show*", "git commit*", "git stash", "git fetch*", "ls*"]


@pytest.mark.parametrize(
    "command, option",
    [
        ("git switch feat/x --discard-changes", "--discard-changes"),
        ("git switch feat/x -f", "-f"),
        ("git switch feat/x -qf", "-qf"),
        ("git checkout -b feat/x --force", "--force"),
        ("git checkout -B feat/x", "-B"),
        ("git branch -d --force feat/x", "--force"),
        ("git branch -v -m main old", "-m"),
        ("git branch -df feat/x", "-df"),
        ("git branch -u origin/feat/x", "-u"),
        ("git tag --delete v1.0.0", "--delete"),
        ("git tag v1.0.0 --force", "--force"),
        ("git fetch --force", "--force"),
        ("git worktree remove .claude/worktrees/x --force", "--force"),
        ("git worktree add .claude/worktrees/x -B main origin/feat/x", "-B"),
        ("git add -f .env.local", "-f"),
        ("git add -u", "-u"),
        ("git commit -m 'x' --amend", "--amend"),
        ("git commit -n -m 'x'", "-n"),
        ("git commit -m 'x' -a", "-a"),
        ("git diff --output=README.md", "--output=README.md"),
        ("git log --output README.md", "--output"),
        ("git grep -Oless pattern", "-Oless"),
        ("cd src && git switch feat/x -f", "-f"),
        ("git fetch origin --upload-pack=sh", "--upload-pack=sh"),
    ],
)
def test_check_forbidden_options_with_forcing_option_exits_2(
    command: str, option: str, capsys: pytest.CaptureFixture
):
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_forbidden_options(command)
    assert blocked.value.code == 2
    assert f"'{option}'" in capsys.readouterr().err


@pytest.mark.parametrize(
    "command",
    ["git fetch origin feat/x:main", "git fetch origin +feat/x:main"],
)
def test_check_forbidden_options_with_fetch_into_a_local_branch_exits_2(
    command: str, capsys: pytest.CaptureFixture
):
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_forbidden_options(command)
    assert blocked.value.code == 2
    assert "local branch" in capsys.readouterr().err


@pytest.mark.parametrize(
    "command",
    [
        "git switch feat/x",
        "git switch -c feat/x",
        "git checkout -b feat/x origin/main",
        "git branch -d old",
        "git branch -vv",
        "git branch --show-current",
        "git tag -a v1.0.0 -m 'release'",
        "git tag -l 'v*'",
        "git fetch origin",
        "git fetch origin main",
        "git worktree add .claude/worktrees/x -b feat/x origin/main",
        "git worktree remove .claude/worktrees/x",
        "git add src/app.py",
        "git commit -m 'add -f handling'",
        "git diff -M -C",
        "git log --oneline -5",
        "git grep -n -i Order",
        "git status",
        "git",
        "ls -f",
        "git commit -m 'unbalanced",
    ],
)
def test_check_forbidden_options_with_safe_command_does_not_block(command: str):
    assert git_guard.check_forbidden_options(command) is None


@pytest.mark.parametrize(
    "command", ["git add ./", "git add :/", "git add -- .", "git add '*'", "git add ."]
)
def test_check_forbidden_options_with_add_of_everything_exits_2(
    command: str, capsys: pytest.CaptureFixture
):
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_forbidden_options(command)
    assert blocked.value.code == 2
    assert "stages every change" in capsys.readouterr().err


@pytest.mark.parametrize(
    "command, subcommand",
    [
        ("git difftool --extcmd=less -y", "difftool"),
        ("git show-ref", "show-ref"),
        ("git commit-tree HEAD^{tree}", "commit-tree"),
        ("cd src && git fetch-pack origin", "fetch-pack"),
        ("git -C /tmp status", "-C"),
    ],
)
def test_check_git_subcommand_with_subcommand_matched_only_by_prefix_exits_2(
    command: str, subcommand: str, capsys: pytest.CaptureFixture
):
    with pytest.raises(SystemExit) as blocked:
        git_guard.check_git_subcommand(command, ALLOW_PATTERNS)
    assert blocked.value.code == 2
    assert f"'git {subcommand}'" in capsys.readouterr().err


@pytest.mark.parametrize(
    "command",
    ["git diff --stat", "git show HEAD", "git stash", "git fetch origin", "ls -la", "git"],
)
def test_check_git_subcommand_with_named_subcommand_does_not_block(command: str):
    assert git_guard.check_git_subcommand(command, ALLOW_PATTERNS) is None
