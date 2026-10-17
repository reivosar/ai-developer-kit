"""Tests for template_guard: which templates a body is held to, and the kit's own."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_guard  # noqa: E402
from template_guard import required_sections  # noqa: E402

HOOKS_DIR = Path(__file__).parent
DEFAULTS = HOOKS_DIR.parent / "templates" / "github"
PUBLISHED = HOOKS_DIR.parents[1] / ".github"
TEMPLATE_NAMES = [
    "PULL_REQUEST_TEMPLATE.md",
    "ISSUE_TEMPLATE/bug_report.md",
    "ISSUE_TEMPLATE/feature_request.md",
    "ISSUE_TEMPLATE/kit_feedback.md",
]
COMPLETE_BODY = "## What\n\nAdds the guard.\n\n## Why\n\nNothing checked the body.\n"
DEFAULT_PR_BODY = (
    "## What\n\nAdds the guard.\n\n## Why\n\nNothing checked the body.\n\n"
    "## Verification\n\npytest passed.\n\n## Breaking changes\n\nNone.\n"
)
FEATURE_BODY = "## Problem\n\nReviewers cannot filter.\n\n## Acceptance criteria\n\nA filter.\n"
KIT_FEEDBACK_BODY = "## Insight\n\nA rule is missing.\n\n## Context\n\nProject: shop.\n"
PR_FILE = "gh pr create --title t --body-file body.md"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    templates = tmp_path / ".github" / "ISSUE_TEMPLATE"
    templates.mkdir(parents=True)
    (templates / "bug.md").write_text(
        "## Steps to reproduce\n\n<!-- Steps. -->\n\n## Actual result\n\n<!-- Seen. -->\n"
    )
    (templates / "feature.md").write_text(
        "## Problem\n\n<!-- Who. -->\n\n## Acceptance criteria\n\n<!-- Then. -->\n"
    )
    return tmp_path


def _blocked_reasons(capsys: pytest.CaptureFixture, command: str) -> str:
    with pytest.raises(SystemExit) as blocked:
        template_guard.check_description(command)
    assert blocked.value.code == 2
    return capsys.readouterr().err


@pytest.mark.parametrize(
    "location",
    [
        ".github/pull_request_template.md",
        "pull_request_template.md",
        "docs/PULL_REQUEST_TEMPLATE.md",
    ],
)
def test_check_description_reads_the_project_template_from_each_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture,
    location: str,
):
    monkeypatch.chdir(tmp_path)
    template = tmp_path / location
    template.parent.mkdir(exist_ok=True)
    template.write_text("## Motivation\n\n<!-- Why. -->\n")
    (tmp_path / "body.md").write_text(COMPLETE_BODY)
    assert "missing section '## Motivation'" in _blocked_reasons(capsys, PR_FILE)


def test_check_description_in_project_without_template_uses_the_kit_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "body.md").write_text(COMPLETE_BODY)
    reasons = _blocked_reasons(capsys, PR_FILE)
    assert "missing section '## Verification'" in reasons
    assert "missing section '## Breaking changes'" in reasons


def test_check_description_with_body_following_the_kit_template_does_not_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "body.md").write_text(DEFAULT_PR_BODY)
    assert template_guard.check_description(PR_FILE) is None


@pytest.mark.parametrize("body", [FEATURE_BODY, KIT_FEEDBACK_BODY])
def test_check_description_with_issue_following_one_template_does_not_block(
    project: Path, body: str
):
    (project / "body.md").write_text(body)
    command = "gh issue create --title 'Filter the list' --body-file body.md"
    assert template_guard.check_description(command) is None


def test_check_description_with_issue_following_no_template_names_the_closest(
    project: Path, capsys: pytest.CaptureFixture
):
    (project / "body.md").write_text("## Problem\n\nReviewers cannot filter.\n")
    reasons = _blocked_reasons(capsys, "gh issue create --title t --body-file body.md")
    assert "feature.md" in reasons
    assert "missing section '## Acceptance criteria'" in reasons
    assert "Steps to reproduce" not in reasons


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_required_sections_of_each_kit_template_names_at_least_two(name: str):
    assert len(required_sections((DEFAULTS / name).read_text())) >= 2


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_published_template_is_identical_to_the_kit_template(name: str):
    assert (PUBLISHED / name).read_text() == (DEFAULTS / name).read_text()


def test_pre_bash_with_pull_request_body_missing_sections_exits_2():
    command = 'gh pr create --title "Add the guard" --body "## What\n\nAdds it.\n"'
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "pre-bash.py")], input=payload,
        capture_output=True, text=True, env={**os.environ, "RATE_LIMIT_DISABLE": "1"},
    )
    assert result.returncode == 2, result.stderr
    assert "missing section '## Why'" in result.stderr
