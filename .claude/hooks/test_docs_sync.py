"""Consistency tests: README.md and CLAUDE.md name only what exists."""
import re
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]
CLAUDE_DIR = KIT_ROOT / ".claude"
SCRIPT_NAME = re.compile(r"[\w-]+\.(?:py|sh)\b")
BACKTICKED_MARKDOWN_NAME = re.compile(r"`[^`\s]*?([\w-]+\.md)`")


def _is_kit_file(path: Path) -> bool:
    relative_parts = path.relative_to(CLAUDE_DIR).parts
    return path.is_file() and "worktrees" not in relative_parts


def _existing_file_names() -> set[str]:
    kit_files = filter(_is_kit_file, CLAUDE_DIR.rglob("*"))
    root_files = filter(Path.is_file, KIT_ROOT.iterdir())
    return {path.name for path in (*kit_files, *root_files)}


def _read_doc(doc_name: str) -> str:
    return (KIT_ROOT / doc_name).read_text()


def _referenced_file_names(doc_text: str) -> set[str]:
    script_names = SCRIPT_NAME.findall(doc_text)
    markdown_names = BACKTICKED_MARKDOWN_NAME.findall(doc_text)
    return set(script_names) | set(markdown_names)


@pytest.mark.parametrize("doc_name", ["README.md", "CLAUDE.md"])
def test_referenced_file_names_in_kit_doc_all_exist(doc_name: str) -> None:
    referenced = _referenced_file_names(_read_doc(doc_name))
    missing = sorted(referenced - _existing_file_names())
    assert not missing, f"{doc_name} names missing files: {missing}"


def test_claude_md_test_list_includes_every_hook_test_file() -> None:
    doc_text = _read_doc("CLAUDE.md")
    test_files = sorted((CLAUDE_DIR / "hooks").glob("test_*.py"))
    unlisted = [path.name for path in test_files if path.name not in doc_text]
    assert not unlisted, f"CLAUDE.md omits hook tests: {unlisted}"


def test_readme_usage_table_includes_every_skill() -> None:
    doc_text = _read_doc("README.md")
    skill_dirs = filter(Path.is_dir, (CLAUDE_DIR / "skills").iterdir())
    skill_names = sorted(path.name for path in skill_dirs)
    unlisted = [name for name in skill_names if f"`/{name}`" not in doc_text]
    assert not unlisted, f"README.md usage table omits skills: {unlisted}"
