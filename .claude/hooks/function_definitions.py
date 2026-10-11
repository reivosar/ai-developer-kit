#!/usr/bin/env python3
"""Locate function definitions in source text by file extension."""
import os
import re

_KEYWORD_SKIP = {
    'if', 'for', 'while', 'return', 'new', 'switch', 'catch', 'try',
    'else', 'do', 'case', 'break', 'continue', 'throw', 'import',
    'class', 'interface', 'enum', 'struct', 'type', 'const', 'let', 'var',
}

_FUNC_PATTERNS: dict[str, list[str]] = {
    '.py':    [r'def\s+(\w+)\s*\('],
    '.go':    [r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\('],
    '.rb':    [r'def\s+(\w+)'],
    '.rs':    [r'fn\s+(\w+)\s*[\(<]'],
    '.kt':    [r'fun\s+(\w+)\s*[\(<]'],
    '.kts':   [r'fun\s+(\w+)\s*[\(<]'],
    '.swift': [r'func\s+(\w+)\s*[\(<]'],
}
_JS_PATTERNS = [
    r'function\s+(\w+)\s*\(',
    r'(?:async\s+)?(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\(',
    r'(?:public|private|protected|static|async)(?:\s+\w+)*\s+(\w+)\s*\(',
]
for _ext in ('.ts', '.tsx', '.js', '.jsx', '.mts', '.mjs'):
    _FUNC_PATTERNS[_ext] = _JS_PATTERNS
_JAVA_PATTERNS = [
    r'(?:public|private|protected|static|final|\s)+\w[\w<>\[\]]*\s+(\w+)\s*\('
]
for _ext in ('.java', '.cs'):
    _FUNC_PATTERNS[_ext] = _JAVA_PATTERNS
_C_PATTERNS = [r'\b(\w+)\s*\([^;]*\)\s*\{']
for _ext in ('.c', '.h', '.cpp', '.cc', '.cxx', '.hpp'):
    _FUNC_PATTERNS[_ext] = _C_PATTERNS


def _line_at(code: str, position: int) -> str:
    start = code.rfind("\n", 0, position) + 1
    end = code.find("\n", position)
    return code[start:len(code) if end == -1 else end].strip()


def _is_function_name(name: str) -> bool:
    return bool(name) and len(name) > 1 and name not in _KEYWORD_SKIP


def find_definitions(code: str, file_path: str) -> dict[str, str]:
    """Return each function name defined in code with its definition line."""
    _, ext = os.path.splitext(file_path)
    definitions: dict[str, str] = {}
    for pattern in _FUNC_PATTERNS.get(ext.lower(), []):
        for match in re.finditer(pattern, code, re.MULTILINE):
            if _is_function_name(match.group(1)):
                position = match.start(1)
                definitions[match.group(1)] = _line_at(code, position)
    return definitions
