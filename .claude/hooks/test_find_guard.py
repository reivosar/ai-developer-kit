"""Tests for find_guard: find may list files, never act on them."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import find_guard  # noqa: E402


@pytest.mark.parametrize(
    "command, action",
    [
        ("find . -name '*.py' -delete", "-delete"),
        ("find . -type f -exec cat {} +", "-exec"),
        ("cd src && find . -execdir ls {} +", "-execdir"),
        ("find . -name '*.md' -fprint found.txt", "-fprint"),
    ],
)
def test_check_find_actions_with_action_that_changes_or_runs_exits_2(
    command: str, action: str, capsys: pytest.CaptureFixture
):
    with pytest.raises(SystemExit) as blocked:
        find_guard.check_find_actions(command)
    assert blocked.value.code == 2
    assert f"find {action}" in capsys.readouterr().err


@pytest.mark.parametrize(
    "command",
    [
        "find . -name '*.md' -not -path '*/.git/*'",
        "find . -path './.claude/docs/*' -type f",
        "grep -r -delete .",
        "find . -name 'unbalanced",
    ],
)
def test_check_find_actions_with_listing_only_does_not_block(command: str):
    assert find_guard.check_find_actions(command) is None
