#!/usr/bin/env python3
"""Guard: block a gh pull request or issue whose body does not follow its template."""
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bash_guard import split_segments  # noqa: E402
from hook_lib import block, read_text  # noqa: E402

KIT_TEMPLATES = Path(__file__).resolve().parent.parent / "templates" / "github"
KIT_PULL_REQUEST_TEMPLATE = KIT_TEMPLATES / "PULL_REQUEST_TEMPLATE.md"
PULL_REQUEST_TEMPLATE_NAME = "pull_request_template.md"
PULL_REQUEST_TEMPLATE_LOCATIONS = (".github", ".", "docs")
ISSUE_TEMPLATES = "ISSUE_TEMPLATE"
OPTIONAL_MARK = "<!-- optional"
BODY_FILE_OPTIONS = ("--body-file", "-F")
BODY_OPTIONS = ("--body", "-b")
KIND_NAMES = {"pr": "pull request", "issue": "issue"}
USE_BODY_FILE = "Write the body to a file from the template and pass it with --body-file."
_DESCRIPTION_RE = re.compile(r"^gh\s+(pr|issue)\s+(create|edit)\b")
_HEADING_RE = re.compile(r"^## .*$", re.MULTILINE)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# A body passed as "$(cat <<'EOF' ... EOF)": the text is what lies between
# the opening line and the end marker.
_HERE_DOCUMENT_RE = re.compile(
    r"\A\$\(cat <<-?\s*['\"]?(?P<marker>\w+)['\"]?\n(?P<text>.*?)(?P=marker)\s*\)\s*\Z",
    re.DOTALL,
)


def _sections(text: str) -> dict[str, str]:
    headings = list(_HEADING_RE.finditer(text))
    ends = [heading.start() for heading in headings[1:]] + [len(text)]
    return {
        heading.group().strip(): text[heading.end():end]
        for heading, end in zip(headings, ends)
    }


def _is_empty(content: str) -> bool:
    return not _COMMENT_RE.sub("", content).strip()


def required_sections(template_text: str) -> list[str]:
    """Return the headings of a template that every body must fill.

    A section is optional when its text starts with the OPTIONAL_MARK comment.
    """
    return [
        heading for heading, content in _sections(template_text).items()
        if not content.strip().startswith(OPTIONAL_MARK)
    ]


def find_problems(body: str, template_text: str) -> list[str]:
    """Return what keeps a body from following a template, one line per problem.

    A required section that the body lacks is missing. A section of the
    template that the body has with nothing in it but comments is empty.
    """
    written = _sections(body)
    missing = [
        f"missing section '{heading}'"
        for heading in required_sections(template_text) if heading not in written
    ]
    empty = [
        f"empty section '{heading}'"
        for heading in _sections(template_text)
        if heading in written and _is_empty(written[heading])
    ]
    return missing + empty


def _words(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def _option_value(words: list[str], options: tuple[str, ...]) -> Optional[str]:
    for index, word in enumerate(words):
        name, separator, value = word.partition("=")
        if name not in options:
            continue
        if separator:
            return value
        return words[index + 1] if index + 1 < len(words) else ""
    return None


def _read_body_file(name: str) -> str:
    try:
        return read_text(name)
    except OSError as error:
        block(f"The body file '{name}' cannot be read.", str(error))


def _inline_body(value: str) -> str:
    here_document = _HERE_DOCUMENT_RE.match(value)
    return here_document.group("text") if here_document else value


def _body(segment: str) -> Optional[str]:
    words = _words(segment)
    body_file = _option_value(words, BODY_FILE_OPTIONS)
    if body_file is not None:
        return _read_body_file(body_file)
    inline = _option_value(words, BODY_OPTIONS)
    return None if inline is None else _inline_body(inline)


def _project_pull_request_template(project: Path) -> Optional[Path]:
    for location in PULL_REQUEST_TEMPLATE_LOCATIONS:
        directory = project / location
        files = sorted(directory.iterdir()) if directory.is_dir() else []
        for candidate in files:
            if candidate.name.lower() == PULL_REQUEST_TEMPLATE_NAME:
                return candidate
    return None


def _templates(kind: str, project: Path) -> list[Path]:
    if kind == "pr":
        return [_project_pull_request_template(project) or KIT_PULL_REQUEST_TEMPLATE]
    own = sorted((project / ".github" / ISSUE_TEMPLATES).glob("*.md"))
    return own + sorted((KIT_TEMPLATES / ISSUE_TEMPLATES).glob("*.md"))


def _closest_template(body: str, templates: list[Path]) -> tuple[Path, list[str]]:
    judged = [
        (template, find_problems(body, read_text(str(template))))
        for template in templates
    ]
    return min(judged, key=lambda judgment: len(judgment[1]))


def _check_body(kind: str, body: str, project: Path) -> None:
    template, problems = _closest_template(body, _templates(kind, project))
    if problems:
        block(
            f"The {KIND_NAMES[kind]} body does not follow the template.",
            *problems, f"Template: {template}", USE_BODY_FILE,
        )


def _check_segment(segment: str, project: Path) -> None:
    described = _DESCRIPTION_RE.match(segment)
    if not described:
        return
    kind, action = described.groups()
    body = _body(segment)
    if body is None and action == "create":
        block(f"gh {kind} create needs a body that follows the template.", USE_BODY_FILE)
    if body is not None:
        _check_body(kind, body, project)


def check_description(command: str) -> None:
    """Block a gh pr or gh issue command whose body does not follow its template.

    The body comes from --body-file or --body. Creating with neither is
    blocked; editing with neither changes no body and is let through. A pull
    request is held to the project's own template, or to the kit's when the
    project has none. An issue passes when it follows any one issue template
    of the project or of the kit. Nothing is checked while
    TEMPLATE_GUARD_DISABLE is set.
    """
    if os.environ.get("TEMPLATE_GUARD_DISABLE"):
        return
    for segment in split_segments(command):
        _check_segment(segment, Path.cwd())
