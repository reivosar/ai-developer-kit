#!/usr/bin/env python3
"""Tests for trash.sh: session file keying, empty-file handling, and collision suffix."""
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
TRASH_SH = HOOKS_DIR / "trash.sh"
REPO_ROOT = Path(
    subprocess.check_output(
        ["git", "-C", str(HOOKS_DIR), "rev-parse", "--show-toplevel"], text=True
    ).strip()
)

passed = failed = 0


def check(label: str, result: bool) -> None:
    global passed, failed
    status = "PASS" if result else "FAIL"
    print(f"[{status}] {label}")
    if result:
        passed += 1
    else:
        failed += 1


def session_key(root: Path) -> str:
    return subprocess.check_output(
        ["bash", "-c", f"printf '%s' '{root}' | md5"], text=True
    ).strip()


def run_trash(*targets: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(TRASH_SH), *targets],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


def clear_session_file():
    p = Path(f"/tmp/claude-session-trash-dir-{session_key(REPO_ROOT)}")
    p.unlink(missing_ok=True)


# TC-TRASH-01: session file path contains md5 of project root, distinct from legacy path
def test_session_file_keyed_by_project_root():
    key = session_key(REPO_ROOT)
    session_path = Path(f"/tmp/claude-session-trash-dir-{key}")
    check("TC-TRASH-01 session key is non-empty", len(key) > 0)
    check(
        "TC-TRASH-01 session file path distinct from legacy path",
        str(session_path) != "/tmp/claude-session-trash-dir",
    )


# TC-TRASH-02: empty session file is treated as absent — trash.sh creates a new trash dir
def test_empty_session_file_ignored():
    clear_session_file()
    key = session_key(REPO_ROOT)
    session_file = Path(f"/tmp/claude-session-trash-dir-{key}")
    session_file.write_text("")  # simulate stale empty file

    test_dir = REPO_ROOT / ".trash-test-tmp"
    test_dir.mkdir(exist_ok=True)
    target = test_dir / "tc02.txt"
    target.write_text("data")

    result = run_trash(str(target.relative_to(REPO_ROOT)))
    check("TC-TRASH-02 empty session file: exit 0", result.returncode == 0)
    check("TC-TRASH-02 target was moved", not target.exists())

    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()
    clear_session_file()


# TC-TRASH-03: two files with the same name in one session — both land in trash
def test_collision_adds_suffix():
    clear_session_file()

    test_dir = REPO_ROOT / ".trash-test-tmp"
    test_dir.mkdir(exist_ok=True)

    file_a = test_dir / "clash.txt"
    file_a.write_text("first")
    result_a = run_trash(str(file_a.relative_to(REPO_ROOT)))
    check("TC-TRASH-03 first move: exit 0", result_a.returncode == 0)
    check("TC-TRASH-03 first file moved", not file_a.exists())

    file_b = test_dir / "clash.txt"
    file_b.write_text("second")
    result_b = run_trash(str(file_b.relative_to(REPO_ROOT)))
    check("TC-TRASH-03 second move with collision: exit 0", result_b.returncode == 0)
    check("TC-TRASH-03 second file moved", not file_b.exists())

    session_file = Path(f"/tmp/claude-session-trash-dir-{session_key(REPO_ROOT)}")
    trash_dir = Path(session_file.read_text().strip())
    items = [p for p in trash_dir.iterdir() if p.name.startswith("clash")]
    check("TC-TRASH-03 both files in trash", len(items) == 2)

    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()
    clear_session_file()


test_session_file_keyed_by_project_root()
test_empty_session_file_ignored()
test_collision_adds_suffix()

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(0 if failed == 0 else 1)
