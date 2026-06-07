#!/usr/bin/env python3
"""Tests for worktree_guard."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import worktree_guard


def test_allows_file_inside_worktree(tmp_path):
    worktrees_dir = tmp_path / ".claude" / "worktrees"
    worktrees_dir.mkdir(parents=True)
    file_path = str(worktrees_dir / "feat-foo" / "src" / "file.py")
    with patch("worktree_guard.WORKTREES_DIR", worktrees_dir):
        with patch("worktree_guard.block") as mock_block:
            worktree_guard.check(file_path)
            mock_block.assert_not_called()


def test_blocks_file_in_repo_root(tmp_path):
    worktrees_dir = tmp_path / ".claude" / "worktrees"
    worktrees_dir.mkdir(parents=True)
    file_path = str(tmp_path / "src" / "main.py")
    with patch("worktree_guard.WORKTREES_DIR", worktrees_dir):
        with patch("worktree_guard.block") as mock_block:
            mock_block.side_effect = SystemExit(2)
            with pytest.raises(SystemExit):
                worktree_guard.check(file_path)
            mock_block.assert_called_once()


def test_blocks_file_in_claude_dir(tmp_path):
    worktrees_dir = tmp_path / ".claude" / "worktrees"
    worktrees_dir.mkdir(parents=True)
    file_path = str(tmp_path / ".claude" / "skills" / "worktree" / "SKILL.md")
    with patch("worktree_guard.WORKTREES_DIR", worktrees_dir):
        with patch("worktree_guard.block") as mock_block:
            mock_block.side_effect = SystemExit(2)
            with pytest.raises(SystemExit):
                worktree_guard.check(file_path)
            mock_block.assert_called_once()


def test_skips_empty_path():
    with patch("worktree_guard.block") as mock_block:
        worktree_guard.check("")
        mock_block.assert_not_called()


def test_allows_nested_file_inside_worktree(tmp_path):
    worktrees_dir = tmp_path / ".claude" / "worktrees"
    worktrees_dir.mkdir(parents=True)
    file_path = str(worktrees_dir / "fix-bug" / "a" / "b" / "c" / "deep.py")
    with patch("worktree_guard.WORKTREES_DIR", worktrees_dir):
        with patch("worktree_guard.block") as mock_block:
            worktree_guard.check(file_path)
            mock_block.assert_not_called()


def test_bypass_via_env_var(tmp_path, monkeypatch):
    worktrees_dir = tmp_path / ".claude" / "worktrees"
    worktrees_dir.mkdir(parents=True)
    file_path = str(tmp_path / "src" / "main.py")
    monkeypatch.setenv("WORKTREE_GUARD_DISABLE", "1")
    with patch("worktree_guard.WORKTREES_DIR", worktrees_dir):
        with patch("worktree_guard.block") as mock_block:
            worktree_guard.check(file_path)
            mock_block.assert_not_called()
