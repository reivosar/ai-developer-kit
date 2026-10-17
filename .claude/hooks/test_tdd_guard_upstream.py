"""Tests for tdd_guard: a file copied unchanged from the upstream kit needs no test."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tdd_guard  # noqa: E402

CANCEL = "def cancel_order(order_id):\n    return order_id\n"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    upstream = tmp_path / ".upstream" / ".claude" / "hooks" / "order_guard.py"
    upstream.parent.mkdir(parents=True)
    upstream.write_text(CANCEL)
    return tmp_path


def test_check_with_content_identical_to_upstream_clone_does_not_block(
    project: Path,
):
    target = str(project / ".claude" / "hooks" / "order_guard.py")
    assert tdd_guard.check(CANCEL, target) is None


def test_check_with_content_differing_from_upstream_clone_exits_2(
    project: Path,
):
    target = str(project / ".claude" / "hooks" / "order_guard.py")
    with pytest.raises(SystemExit) as blocked:
        tdd_guard.check(CANCEL + "LIMIT = 1\n", target)
    assert blocked.value.code == 2
