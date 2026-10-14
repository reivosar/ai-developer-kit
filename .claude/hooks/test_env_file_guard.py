"""Tests for env_file_guard and content_guard: what a file may not hold or be."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_guard  # noqa: E402
from env_file_guard import is_blocked_env_file  # noqa: E402

HIRAGANA = chr(0x3053) + chr(0x3093)
EMOJI = chr(0x1F600)


@pytest.mark.parametrize(
    "path, blocked",
    [
        (".env", True),
        ("config/.env.local", True),
        (".env.example", False),
        (".env.sample", False),
        ("environment.py", False),
    ],
)
def test_is_blocked_env_file_returns_whether_the_file_holds_secrets(
    path: str, blocked: bool
):
    assert is_blocked_env_file(path) is blocked


def test_check_japanese_with_japanese_text_exits_2(capsys: pytest.CaptureFixture):
    with pytest.raises(SystemExit) as blocked:
        content_guard.check_japanese(f"title = '{HIRAGANA}'", "orders.py")
    assert blocked.value.code == 2
    assert "Japanese characters detected" in capsys.readouterr().err


@pytest.mark.parametrize(
    "content, path",
    [("title = 'orders'", "orders.py"), (HIRAGANA, "src/locale/ja.json")],
)
def test_check_japanese_with_english_or_locale_file_does_not_block(
    content: str, path: str
):
    assert content_guard.check_japanese(content, path) is None


def test_check_emoji_with_emoji_exits_2(capsys: pytest.CaptureFixture):
    with pytest.raises(SystemExit) as blocked:
        content_guard.check_emoji(f"done {EMOJI}", "notes.md")
    assert blocked.value.code == 2
    assert "Emoji detected" in capsys.readouterr().err


def test_check_emoji_with_plain_text_does_not_block():
    assert content_guard.check_emoji("Good: done", "notes.md") is None
