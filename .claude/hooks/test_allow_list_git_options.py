"""Tests for pre-bash.py on options that force or discard, and on hidden commands.

Each case runs pre-bash.py on a feature branch through the pre_bash_blocks
fixture in conftest.py.
"""
import pytest

CASES = [
    # Options that force, delete, or discard
    ("git switch feat/x --discard-changes",    True),
    ("git switch feat/x -f",                   True),
    ("git switch -c feat/x --discard-changes", True),
    ("git checkout -b feat/x --force",         True),
    ("git checkout -b feat/x -f",              True),
    ("git worktree remove .claude/worktrees/x --force", True),
    ("git worktree add .claude/worktrees/x -B main origin/feat/x", True),
    ("git branch -d --force feat/x",           True),
    ("git branch -v --delete --force feat/x",  True),
    ("git branch -v -m main old",              True),
    ("git branch -df feat/x",                  True),
    ("git tag --delete v1.0.0",                True),
    ("git tag v1.0.0 --force",                 True),
    ("git diff --output=README.md",            True),
    ("git log --output README.md",             True),
    ("git grep -Oless pattern",                True),
    ("git commit -m 'x' --amend",              True),
    ("git commit -n -m 'x'",                   True),
    ("git commit -m 'x' -a",                   True),
    ("git add -f .env.local",                  True),
    ("git add -u",                             True),
    ("git difftool --extcmd=less -y",          True),
    ("git show-ref",                           True),
    ("git fetch origin --upload-pack=sh",      True),
    ("git add ./",                             True),
    ("git add src/app.py",                     False),
    ("git status $'\\'' ; gh pr close 1 #'",   True),
    ("gh label create bug --force",            True),
    ("gh pr comment 1 --delete-last --yes",    True),
    ("gh pr comment 1 --body 'looks good'",    False),
    # find may list files, never act on them
    ("find . -name '*.py' -delete",            True),
    ("find . -type f -exec cat {} +",          True),
    ("find . -name '*.md' -not -path '*/.git/*'", False),
    # Shell syntax that runs a command the allow list never sees
    ("git status $(gh pr close 1)",            True),
    ("git status `gh pr close 1`",             True),
    ('git log --format="$(gh pr close 1)"',    True),
    ("cat <(gh pr close 1)",                   True),
    ("git status & gh pr close 1",             True),
    ("git status\ngh pr close 1",              True),
    ('git status \\" && gh pr close 1 \\"',    True),
    ("git log --format='%h $(not run)'",       False),
    ("gh issue list \\\n  --label bug",        False),
    ('grep -n "a\\|b" README.md',              False),
    ('grep -n "say \\"hi\\" | now" README.md', False),
    ("git mergetool",                True),
    ("git restore .",                True),
    ("git restore README.md",        True),
    ("git reset",                    True),
    ("git reset HEAD file.txt",      True),
    ("git push",                          True),
    ("git push -u origin HEAD",           False),
    ("git push origin HEAD",              False),
    ("git push origin HEAD:main",         True),
    ("git push upstream main",            True),
    ("git push origin refs/heads/main",   True),
    # Commands that take in everything, rewrite history, or skip the hooks
    ("git add .",                               True),
    ("git add -A",                              True),
    ("git add -A .",                            True),
    ("git add --all",                           True),
    ("git commit -a -m 'x'",                    True),
    ("git commit -am 'x'",                      True),
    ("git commit --all -m 'x'",                 True),
    ("git commit --amend",                      True),
    ("git commit --no-verify -m 'x'",           True),
    ("git pull --ff-only",                      False),
    ("git pull --ff-only origin main",          False),
    ("git pull --force",                        True),
    ("git pull --rebase",                       True),
]


@pytest.mark.parametrize("command, blocked", CASES)
def test_pre_bash_with_forcing_option_or_hidden_command_blocks(
    pre_bash_blocks, command: str, blocked: bool
):
    assert pre_bash_blocks(command) is blocked
