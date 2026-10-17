"""Tests for template_guard: gh pull request and issue bodies follow a template."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_guard  # noqa: E402
from template_guard import find_problems, required_sections  # noqa: E402

TEMPLATE = (
    "---\nname: Change\n---\n"
    "## What\n\n<!-- What changed. -->\n\n"
    "## Why\n\n<!-- The problem. -->\n\n"
    "## Known limits\n\n<!-- optional: delete this section when it is empty. -->\n"
)
COMPLETE_BODY = "## What\n\nAdds the guard.\n\n## Why\n\nNothing checked the body.\n"
BODY_WITHOUT_WHY = "## What\n\nAdds the guard and mentions ## Why inline.\n"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text(TEMPLATE)
    return tmp_path


def _blocked_reasons(capsys: pytest.CaptureFixture, command: str) -> str:
    with pytest.raises(SystemExit) as blocked:
        template_guard.check_description(command)
    assert blocked.value.code == 2
    return capsys.readouterr().err


def test_required_sections_with_optional_section_leaves_it_out():
    assert required_sections(TEMPLATE) == ["## What", "## Why"]


def test_find_problems_with_every_required_section_filled_returns_nothing():
    assert find_problems(COMPLETE_BODY, TEMPLATE) == []


def test_find_problems_with_heading_only_inside_a_line_reports_it_missing():
    assert find_problems(BODY_WITHOUT_WHY, TEMPLATE) == ["missing section '## Why'"]


def test_find_problems_with_section_holding_only_a_comment_reports_it_empty():
    body = COMPLETE_BODY.replace("Nothing checked the body.", "<!-- The problem. -->")
    assert find_problems(body, TEMPLATE) == ["empty section '## Why'"]


def test_find_problems_with_optional_section_left_empty_reports_it_empty():
    body = COMPLETE_BODY + "\n## Known limits\n\n<!-- optional: delete it. -->\n"
    assert find_problems(body, TEMPLATE) == ["empty section '## Known limits'"]


def test_find_problems_with_optional_section_filled_returns_nothing():
    body = COMPLETE_BODY + "\n## Known limits\n\nIssue forms are not read.\n"
    assert find_problems(body, TEMPLATE) == []


@pytest.mark.parametrize(
    "command", ["git status", "gh pr list", "gh pr edit 12 --add-label bug"]
)
def test_check_description_with_command_that_sets_no_body_does_not_block(
    project: Path, command: str
):
    assert template_guard.check_description(command) is None


def test_check_description_with_complete_body_file_does_not_block(project: Path):
    (project / "body.md").write_text(COMPLETE_BODY)
    command = "gh pr create --title 'Add the guard' --body-file body.md"
    assert template_guard.check_description(command) is None


@pytest.mark.parametrize(
    "command",
    [
        "gh pr create --title 'Add the guard' --body-file body.md",
        "gh pr create --title 'Add the guard' -F body.md",
        "gh pr create --title 'Add the guard' --body-file=body.md",
        "gh pr edit 12 --body-file body.md",
        "cd service && gh pr create --title 'Add the guard' --body-file body.md",
    ],
)
def test_check_description_with_body_file_missing_a_section_exits_2(
    project: Path, capsys: pytest.CaptureFixture, command: str
):
    (project / "body.md").write_text(BODY_WITHOUT_WHY)
    reasons = _blocked_reasons(capsys, command)
    assert "missing section '## Why'" in reasons
    assert "PULL_REQUEST_TEMPLATE.md" in reasons


@pytest.mark.parametrize(
    "command",
    ["gh pr create --title 'Add the guard'", "gh pr create --fill", "gh issue create"],
)
def test_check_description_creating_without_a_body_exits_2(
    project: Path, capsys: pytest.CaptureFixture, command: str
):
    assert "--body-file" in _blocked_reasons(capsys, command)


def test_check_description_with_body_file_that_cannot_be_read_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    reasons = _blocked_reasons(capsys, "gh pr create --title t --body-file absent.md")
    assert "absent.md" in reasons


def test_check_description_with_complete_inline_body_does_not_block(project: Path):
    command = f'gh pr create --title "Add the guard" --body "{COMPLETE_BODY}"'
    assert template_guard.check_description(command) is None


def test_check_description_with_inline_body_missing_a_section_exits_2(
    project: Path, capsys: pytest.CaptureFixture
):
    command = f"gh pr create --title t --body \"$(cat <<'EOF'\n{BODY_WITHOUT_WHY}EOF\n)\""
    assert "missing section '## Why'" in _blocked_reasons(capsys, command)


def _here_document_command(body: str, opening: str = "<<'EOF'", marker: str = "EOF") -> str:
    return f'gh pr create --title t --body "$(cat {opening}\n{body}{marker}\n)"'


@pytest.mark.parametrize(
    "opening, marker",
    [("<<'EOF'", "EOF"), ("<<EOF", "EOF"), ("<<-'EOF'", "EOF"), ("<<'BODY'", "BODY")],
)
def test_check_description_with_here_document_and_empty_last_section_exits_2(
    project: Path, capsys: pytest.CaptureFixture, opening: str, marker: str
):
    body = "## What\n\nAdds the guard.\n\n## Why\n\n"
    command = _here_document_command(body, opening, marker)
    assert "empty section '## Why'" in _blocked_reasons(capsys, command)


def test_check_description_with_complete_here_document_body_does_not_block(
    project: Path,
):
    command = _here_document_command(COMPLETE_BODY)
    assert template_guard.check_description(command) is None


def test_check_description_with_here_document_text_naming_the_marker_keeps_it(
    project: Path,
):
    body = "## What\n\nAdds the guard.\n\n## Why\n\nThe EOF marker was read as text.\n"
    command = _here_document_command(body)
    assert template_guard.check_description(command) is None


def test_check_description_with_guard_disabled_does_not_block(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("TEMPLATE_GUARD_DISABLE", "1")
    assert template_guard.check_description("gh pr create --fill") is None
