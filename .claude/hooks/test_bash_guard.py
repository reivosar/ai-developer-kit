"""Tests for bash_guard: command segments and the script path check."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bash_guard  # noqa: E402


@pytest.mark.parametrize(
    "command, segments",
    [
        ("git status", ["git status"]),
        ("cd a && cd b", ["cd a", "cd b"]),
        ("a; b | c", ["a", "b", "c"]),
        ("a || b", ["a", "b"]),
        ("a &&", ["a"]),
        ("a & b", ["a & b"]),
        ("echo 'a;b'", ["echo 'a;b'"]),
        ('echo "a && b"', ['echo "a && b"']),
        ("echo \"it's; fine\" ; ls", ["echo \"it's; fine\"", "ls"]),
        ("echo 'say \"hi\" | now' | wc", ["echo 'say \"hi\" | now'", "wc"]),
    ],
)
def test_split_segments_splits_on_separators_outside_quotes(
    command: str, segments: list
):
    assert bash_guard.split_segments(command) == segments


@pytest.mark.parametrize("command", ["", " ; ", "&&"])
def test_split_segments_with_no_segment_returns_the_command(command: str):
    assert bash_guard.split_segments(command) == [command]


@pytest.mark.parametrize(
    "command, segments",
    [
        ('git status \\" && gh pr close 1 \\"', ['git status \\"', 'gh pr close 1 \\"']),
        ('grep "a\\"b; c" notes.md', ['grep "a\\"b; c" notes.md']),
        ("echo a\\;b", ["echo a\\;b"]),
        ("echo 'a\\' ; ls", ["echo 'a\\'", "ls"]),
    ],
)
def test_split_segments_with_backslash_reads_the_next_character_as_text(
    command: str, segments: list
):
    assert bash_guard.split_segments(command) == segments


@pytest.mark.parametrize(
    "command, problem",
    [
        ("git diff > patch.txt", "shell redirect operator '>'"),
        ("git log | wc", "pipe operator '|'"),
        ("git status $(gh pr close 1)", "command substitution"),
        ("git status `gh pr close 1`", "command substitution"),
        ('git log --format="$(gh pr close 1)"', "command substitution"),
        ("cat <(gh pr close 1)", "process substitution"),
        ("git status & gh pr close 1", "background operator '&'"),
        ("git status\ngh pr close 1", "second command line"),
        ('git status \\" | gh pr close 1 \\"', "pipe operator '|'"),
        ("git status $'\\'' ; gh pr close 1 #'", "ANSI-C quoting"),
    ],
)
def test_check_raw_operators_with_syntax_that_runs_another_command_exits_2(
    command: str, problem: str, capsys: pytest.CaptureFixture
):
    with pytest.raises(SystemExit) as blocked:
        bash_guard.check_raw_operators(command)
    assert blocked.value.code == 2
    assert problem in capsys.readouterr().err


@pytest.mark.parametrize(
    "command",
    [
        "git log --format='%h $(not run) `nor this`'",
        'git commit -m "first line\n\nsecond paragraph"',
        "gh issue list \\\n  --label bug",
        'grep -n "a\\|b" README.md',
        'grep -n "say \\"hi\\" | now" README.md',
        "git status && git log",
        "echo 'a & b > c'",
        "git log --format=%h\n",
    ],
)
def test_check_raw_operators_with_quoted_or_escaped_syntax_does_not_block(
    command: str,
):
    assert bash_guard.check_raw_operators(command) is None


@pytest.mark.parametrize(
    "command, reason",
    [
        (
            "python3 /tmp/evil.py",
            "python3: absolute path '/tmp/evil.py' is not permitted."
            " Use a relative path within the project.",
        ),
        (
            "cd src && python3 ../attack.py",
            "python3: path traversal '../attack.py' is not permitted.",
        ),
        (
            "pytest -q .claude/worktrees/feat-foo/test_api.py",
            "pytest: scripts under .claude/worktrees/ must be run from inside"
            " the worktree using a relative path.",
        ),
        (
            "python3 -m pytest tests/ /tmp/test_evil.py",
            "python3: absolute path '/tmp/test_evil.py' is not permitted."
            " Use a relative path within the project.",
        ),
    ],
)
def test_check_python3_path_with_script_outside_project_exits_2(
    command: str, reason: str, capsys: pytest.CaptureFixture
):
    with pytest.raises(SystemExit) as blocked:
        bash_guard.check_python3_path(command)
    assert blocked.value.code == 2
    assert capsys.readouterr().err == (
        f"BLOCKED: {reason}\n  Command: {command}\n"
    )


@pytest.mark.parametrize(
    "command",
    [
        "python3 tests/test_foo.py",
        "pytest",
        "pytest --cov=. --cov-branch",
        "pytest tests/",
        "python3 --version",
        "python3 'unbalanced.py",
        "cat /tmp/notes.py",
        "python3 tests/test_foo.py /tmp/second.py",
    ],
)
def test_check_python3_path_with_script_inside_project_does_not_block(
    command: str,
):
    assert bash_guard.check_python3_path(command) is None
