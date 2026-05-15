"""Shared hook utilities for Python hooks."""
from pathlib import Path

# .claude/hooks/hook_lib.py -> .claude/hooks -> .claude -> repo root
REPO_ROOT: Path = Path(__file__).resolve().parents[2]
WORKTREES_DIR: Path = REPO_ROOT / ".claude" / "worktrees"
