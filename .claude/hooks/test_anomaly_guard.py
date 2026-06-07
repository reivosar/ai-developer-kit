"""Tests for anomaly_guard.check_sensitive_path and check_path_escape."""
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = str(Path(__file__).resolve().parent)


def _sensitive_exit(command: str) -> int:
    script = (
        f"import sys; sys.path.insert(0, {HOOKS_DIR!r})\n"
        f"import anomaly_guard\n"
        f"anomaly_guard.check_sensitive_path({command!r})\n"
    )
    return subprocess.run([sys.executable, "-c", script], capture_output=True).returncode


def _escape_exit(path: str) -> int:
    script = (
        f"import sys; sys.path.insert(0, {HOOKS_DIR!r})\n"
        f"import anomaly_guard\n"
        f"anomaly_guard.check_path_escape({path!r})\n"
    )
    return subprocess.run([sys.executable, "-c", script], capture_output=True).returncode


def test_check_sensitive_path_with_ssh_key_blocks():
    assert _sensitive_exit("cat ~/.ssh/id_rsa") == 2


def test_check_sensitive_path_with_ssh_config_blocks():
    assert _sensitive_exit("cat ~/.ssh/config") == 2


def test_check_sensitive_path_with_aws_credentials_blocks():
    assert _sensitive_exit("cat ~/.aws/credentials") == 2


def test_check_sensitive_path_with_etc_passwd_blocks():
    assert _sensitive_exit("cat /etc/passwd") == 2


def test_check_sensitive_path_with_etc_shadow_blocks():
    assert _sensitive_exit("grep root /etc/shadow") == 2


def test_check_sensitive_path_with_etc_hosts_blocks():
    assert _sensitive_exit("cat /etc/hosts") == 2


def test_check_sensitive_path_with_expanded_ssh_path_blocks():
    assert _sensitive_exit("cat /Users/mac/.ssh/id_rsa") == 2


def test_check_sensitive_path_with_expanded_aws_path_blocks():
    assert _sensitive_exit("cat /home/deploy/.aws/credentials") == 2


def test_check_sensitive_path_with_normal_git_command_passes():
    assert _sensitive_exit("git status") == 0


def test_check_sensitive_path_with_empty_command_passes():
    assert _sensitive_exit("") == 0


def test_check_path_escape_with_path_inside_repo_passes():
    script = (
        f"import sys; sys.path.insert(0, {HOOKS_DIR!r})\n"
        f"from hook_lib import REPO_ROOT\n"
        f"import anomaly_guard\n"
        f"anomaly_guard.check_path_escape(str(REPO_ROOT / '.claude' / 'hooks' / 'test.py'))\n"
    )
    assert subprocess.run([sys.executable, "-c", script], capture_output=True).returncode == 0


def test_check_path_escape_with_tmp_path_blocks():
    assert _escape_exit("/tmp/malicious_file.py") == 2


def test_check_path_escape_with_home_directory_blocks():
    assert _escape_exit("/Users/mac/.ssh/known_hosts") == 2


def test_check_path_escape_with_empty_path_passes():
    assert _escape_exit("") == 0


def test_check_sensitive_path_in_quoted_commit_message_passes():
    assert _sensitive_exit('git commit -m "mentions ~/.ssh/ in commit docs"') == 0


def test_check_sensitive_path_unquoted_still_blocks():
    assert _sensitive_exit("cat ~/.ssh/id_rsa") == 2
