#!/usr/bin/env python3
"""TDD red-phase guard: blocks impl edits unless staged tests cover the modified functions."""
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402

_IMPL_EXTS = {
    '.ts', '.tsx', '.js', '.jsx', '.mts', '.mjs',
    '.py', '.go', '.java', '.rb', '.rs',
    '.kt', '.kts', '.swift', '.cs',
    '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.php',
}
_SKIP_BASENAMES = {'Makefile', 'Dockerfile', 'Procfile', '.gitignore'}
_SKIP_EXT = {'.md', '.json', '.yaml', '.yml', '.toml', '.ini', '.sh',
             '.txt', '.lock', '.sum', '.env', '.gitignore'}
_TEST_NAME_RE = re.compile(r'(test|spec)(\.|_|-|$)', re.IGNORECASE)
_TEST_DIR_RE = re.compile(r'(/__tests__/|/tests?/|/specs?/)', re.IGNORECASE)
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
_JAVA_PATTERNS = [r'(?:public|private|protected|static|final|\s)+\w[\w<>\[\]]*\s+(\w+)\s*\(']
for _ext in ('.java', '.cs'):
    _FUNC_PATTERNS[_ext] = _JAVA_PATTERNS
_C_PATTERNS = [r'\b(\w+)\s*\([^;]*\)\s*\{']
for _ext in ('.c', '.h', '.cpp', '.cc', '.cxx', '.hpp'):
    _FUNC_PATTERNS[_ext] = _C_PATTERNS


def _is_test_file(path: str) -> bool:
    return bool(_TEST_NAME_RE.search(os.path.basename(path)) or _TEST_DIR_RE.search(path))


def _is_impl_file(path: str) -> bool:
    basename = os.path.basename(path)
    if basename in _SKIP_BASENAMES:
        return False
    if '.claude' in Path(path).parts or path.startswith('CLAUDE'):
        return False
    _, ext = os.path.splitext(path)
    if ext.lower() in _SKIP_EXT or not ext or path.startswith('.env'):
        return False
    if _is_test_file(path):
        return False
    return ext.lower() in _IMPL_EXTS


def _extract_func_names(code: str, file_path: str) -> set[str]:
    _, ext = os.path.splitext(file_path)
    names: set[str] = set()
    for pattern in _FUNC_PATTERNS.get(ext.lower(), []):
        for m in re.finditer(pattern, code, re.MULTILINE):
            name = m.group(1)
            if name and len(name) > 1 and name not in _KEYWORD_SKIP:
                names.add(name)
    return names


def _git_files(cmd: list[str]) -> list[str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return [f for f in result.stdout.strip().split('\n') if f]
    except Exception:
        return []


def _test_covers_funcs(test_paths: list[str], func_names: set[str]) -> bool:
    for path in test_paths:
        try:
            with open(path, encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if any(name in content for name in func_names):
                return True
        except OSError:
            continue
    return False


def _fail(reason: str, file_path: str, func_names: set[str], staged_tests: list[str]) -> None:
    details = [f"File: {file_path}"]
    if func_names:
        details.append(f"Functions being modified: {', '.join(sorted(func_names))}")
    if staged_tests:
        details.append(f"Staged tests: {', '.join(staged_tests)}")
        details.append("None reference the modified functions.")
    else:
        details.append("No test files staged or in the last commit.")
    details.append("Write a failing test for these functions first (Red phase).")
    hook_lib.block(reason, *details)


def check(code: str, file_path: str) -> None:
    if not _is_impl_file(file_path) or not code:
        return
    func_names = _extract_func_names(code, file_path)
    staged = [f for f in _git_files(['git', 'diff', '--staged', '--name-only']) if _is_test_file(f)]
    last = [f for f in _git_files(['git', 'log', '-1', '--name-only', '--pretty=format:']) if _is_test_file(f)]
    all_tests = staged + last
    if not all_tests:
        _fail("No test files staged.", file_path, func_names, staged)
    if func_names:
        if not _test_covers_funcs(all_tests, func_names):
            _fail("Staged tests do not reference the modified functions.", file_path, func_names, staged)
    else:
        stem = re.sub(r'\.\w+$', '', os.path.basename(file_path)).lower()
        if not any(stem in os.path.basename(t).lower() for t in all_tests):
            _fail(f"No test for '{os.path.basename(file_path)}' found.", file_path, func_names, staged)
