#!/usr/bin/env python3
"""The shapes doc_comments reads: a found definition, and each language's syntax."""
from typing import NamedTuple, Optional

_NEVER = r"(?!)"


class Definition(NamedTuple):
    """A public function, method, or type as the doc comment rules see it."""

    name: str
    doc: Optional[str]  # None when the definition has no doc comment
    params: Optional[tuple]  # None when the parameters cannot be read
    # Read for Python only, where Google style asks for Returns, Yields, Raises.
    returns: bool = False  # the body returns a value other than None
    yields: bool = False  # the body is a generator
    raised: tuple = ()  # names of the exceptions the body raises itself


class Language(NamedTuple):
    """How one language marks a public definition and its doc comment."""

    definitions: tuple  # regexes with a group "name"; one ending in "(" is callable
    param_name: Optional[str] = None  # regex with a group "name", per parameter
    doc_prefix: Optional[str] = None  # the doc comment is a run of such lines
    inherits_doc: str = _NEVER  # marks a definition documented where it is declared


_ANNOTATIONS = r"^[ \t]*(?:@\w+(?:\([^)\n]*\))?[ \t]+)*"
_JAVA = Language(
    definitions=(
        _ANNOTATIONS
        + r"public\b[^;{=()\n]*?\b(?:class|interface|enum)[ \t]+(?P<name>\w+)",
        _ANNOTATIONS + r"public\b[^;{=()\n]*?\b(?P<name>\w+)[ \t]*\(",
    ),
    param_name=r"(?P<name>\w+)[ \t]*(?:\[\])*$",
    inherits_doc=r"@Override\b",
)
_KOTLIN_MODIFIERS = (
    r"^[ \t]*(?:(?:public|open|abstract|final|suspend|inline|operator|infix"
    r"|tailrec|external|data|sealed|enum|annotation|value)[ \t]+)*"
)
_KOTLIN = Language(
    definitions=(
        _KOTLIN_MODIFIERS + r"(?:class|interface|object)[ \t]+(?P<name>\w+)",
        _KOTLIN_MODIFIERS
        + r"fun[ \t]+(?:<[^>\n]+>[ \t]+)?(?:[\w<>?,.]+\.)?(?P<name>\w+)[ \t]*\(",
    ),
    param_name=(
        r"^(?:@\w+[ \t]+)*(?:(?:vararg|noinline|crossinline|val|var)[ \t]+)*"
        r"(?P<name>\w+)[ \t]*:"
    ),
)
_GO = Language(
    definitions=(
        r"^type[ \t]+(?P<name>[A-Z]\w*)\b",
        r"^func[ \t]+(?:\([^)\n]*\)[ \t]*)?(?P<name>[A-Z]\w*)[ \t]*[(\[]",
    ),
    doc_prefix="//",
)
_RUST_QUALIFIERS = r'(?:(?:async|const|unsafe|extern(?:[ \t]+"[^"\n]*")?)[ \t]+)*'
_RUST = Language(
    definitions=(
        r"^[ \t]*pub[ \t]+(?:struct|enum|trait|union)[ \t]+(?P<name>\w+)",
        r"^[ \t]*pub[ \t]+" + _RUST_QUALIFIERS
        + r"fn[ \t]+(?P<name>\w+)[ \t]*(?:<[^(\n]*>)?[ \t]*\(",
    ),
    doc_prefix="///",
)
_JS_NAME = r"(?P<name>[A-Za-z_$][\w$]*)[ \t]*"
_JS_CALL = r"(?:<[^>\n]*>)?[ \t]*\("
_JAVASCRIPT = Language(
    definitions=(
        r"^export[ \t]+(?:default[ \t]+)?(?:abstract[ \t]+)?class[ \t]+" + _JS_NAME,
        r"^export[ \t]+(?:default[ \t]+)?(?:async[ \t]+)?function\*?[ \t]+"
        + _JS_NAME + _JS_CALL,
        r"^export[ \t]+(?:const|let)[ \t]+" + _JS_NAME
        + r"(?::[^=\n]+)?=[ \t]*(?:async[ \t]*)?" + _JS_CALL,
        r"^[ \t]+public[ \t]+(?:(?:static|async|override|abstract)[ \t]+)*"
        + _JS_NAME + _JS_CALL,
    ),
    param_name=(
        r"^(?:(?:public|private|protected|readonly|override)[ \t]+)*"
        r"(?:\.\.\.)?(?P<name>[A-Za-z_$][\w$]*)"
    ),
    inherits_doc=r"\boverride\b",
)

LANGUAGES: dict[str, Language] = {
    ".java": _JAVA, ".kt": _KOTLIN, ".kts": _KOTLIN, ".go": _GO, ".rs": _RUST,
    **{
        extension: _JAVASCRIPT
        for extension in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".mts")
    },
}
