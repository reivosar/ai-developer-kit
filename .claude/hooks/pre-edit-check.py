#!/usr/bin/env python3
"""
TDD Red-phase enforcement hook for Write/Edit tools.
Verifies that staged (or recently committed) test files reference
the functions being modified before allowing implementation edits.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_guard  # noqa: E402
from env_file_guard import is_blocked_env_file  # noqa: E402
from hook_lib import read_stdin_json, block  # noqa: E402

IMPL_EXTS = {
    '.ts', '.tsx', '.js', '.jsx', '.mts', '.mjs',
    '.py', '.go', '.java', '.rb', '.rs',
    '.kt', '.kts', '.swift', '.cs',
    '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.php',
}

SKIP_BASENAMES = {'Makefile', 'Dockerfile', 'Procfile', '.gitignore'}

SKIP_EXT = {'.md', '.json', '.yaml', '.yml', '.toml', '.ini', '.sh',
            '.txt', '.lock', '.sum', '.env', '.gitignore'}

TEST_NAME_RE = re.compile(r'(test|spec)(\.|_|-|$)', re.IGNORECASE)
TEST_DIR_RE = re.compile(r'(/__tests__/|/tests?/|/specs?/)', re.IGNORECASE)

FUNC_PATTERNS = {
    '.py':    [r'def\s+(\w+)\s*\('],
    '.go':    [r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\('],
    '.rb':    [r'def\s+(\w+)'],
    '.rs':    [r'fn\s+(\w+)\s*[\(<]'],
    '.kt':    [r'fun\s+(\w+)\s*[\(<]'],
    '.kts':   [r'fun\s+(\w+)\s*[\(<]'],
    '.swift': [r'func\s+(\w+)\s*[\(<]'],
}
_JS = [
    r'function\s+(\w+)\s*\(',
    r'(?:async\s+)?(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\(',
    r'(?:public|private|protected|static|async)(?:\s+\w+)*\s+(\w+)\s*\(',
]
for _e in ('.ts', '.tsx', '.js', '.jsx', '.mts', '.mjs'):
    FUNC_PATTERNS[_e] = _JS
_JAVA = [r'(?:public|private|protected|static|final|\s)+\w[\w<>\[\]]*\s+(\w+)\s*\(']
for _e in ('.java', '.cs'):
    FUNC_PATTERNS[_e] = _JAVA
_C = [r'\b(\w+)\s*\([^;]*\)\s*\{']
for _e in ('.c', '.h', '.cpp', '.cc', '.cxx', '.hpp'):
    FUNC_PATTERNS[_e] = _C

KEYWORD_SKIP = {'if', 'for', 'while', 'return', 'new', 'switch', 'catch', 'try',
                'else', 'do', 'case', 'break', 'continue', 'throw', 'import',
                'class', 'interface', 'enum', 'struct', 'type', 'const', 'let', 'var'}


def is_impl_file(path: str) -> bool:
    basename = os.path.basename(path)
    if basename in SKIP_BASENAMES:
        return False
    if '.claude' in Path(path).parts or path.startswith('CLAUDE'):
        return False
    _, ext = os.path.splitext(path)
    if ext.lower() in SKIP_EXT:
        return False
    if not ext or path.startswith('.env'):
        return False
    if is_test_file(path):
        return False
    return ext.lower() in IMPL_EXTS


def is_test_file(path: str) -> bool:
    basename = os.path.basename(path)
    return bool(TEST_NAME_RE.search(basename) or TEST_DIR_RE.search(path))


def extract_func_names(code: str, file_path: str) -> set[str]:
    _, ext = os.path.splitext(file_path)
    patterns = FUNC_PATTERNS.get(ext.lower(), [])
    names = set()
    for pattern in patterns:
        for m in re.finditer(pattern, code, re.MULTILINE):
            name = m.group(1)
            if name and len(name) > 1 and name not in KEYWORD_SKIP:
                names.add(name)
    return names


def git_files(cmd: list[str]) -> list[str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return [f for f in result.stdout.strip().split('\n') if f]
    except Exception:
        return []


def test_covers_funcs(test_paths: list[str], func_names: set[str]) -> bool:
    for path in test_paths:
        try:
            with open(path, encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if any(name in content for name in func_names):
                return True
        except OSError:
            continue
    return False


def _fail_tdd(reason: str, file_path: str, func_names: set[str], staged_tests: list[str]) -> None:
    details = [f"File: {file_path}"]
    if func_names:
        details.append(f"Functions being modified: {', '.join(sorted(func_names))}")
    if staged_tests:
        details.append(f"Staged tests: {', '.join(staged_tests)}")
        details.append("None reference the modified functions.")
    else:
        details.append("No test files staged or in the last commit.")
    details.append("Write a failing test for these functions first (Red phase).")
    block(reason, *details)


def main() -> None:
    data = read_stdin_json()
    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})
    file_path = tool_input.get('file_path', '')

    if not file_path:
        sys.exit(0)
    if is_blocked_env_file(file_path):
        block(
            f"'{os.path.basename(file_path)}' must not be written. "
            "Use .env.sample or .env.example instead."
        )
    new_content = tool_input.get("new_string", "")
    content_guard.check_japanese(new_content, file_path)
    content_guard.check_emoji(new_content, file_path)
    if not is_impl_file(file_path):
        sys.exit(0)

    code = (tool_input.get('old_string') or '') if tool_name == 'Edit' else tool_input.get('content', '')
    if not code:
        sys.exit(0)

    func_names = extract_func_names(code, file_path)

    staged_tests = [f for f in git_files(['git', 'diff', '--staged', '--name-only']) if is_test_file(f)]
    last_tests = [f for f in git_files(['git', 'log', '-1', '--name-only', '--pretty=format:']) if is_test_file(f)]
    all_tests = staged_tests + last_tests

    if not all_tests:
        _fail_tdd("No test files staged.", file_path, func_names, staged_tests)

    if func_names:
        if not test_covers_funcs(all_tests, func_names):
            _fail_tdd(
                "Staged tests do not reference the modified functions.",
                file_path, func_names, staged_tests,
            )
    else:
        impl_stem = re.sub(r'\.\w+$', '', os.path.basename(file_path)).lower()
        matched = [t for t in all_tests if impl_stem in os.path.basename(t).lower()]
        if not matched:
            _fail_tdd(
                f"No test for '{os.path.basename(file_path)}' found.",
                file_path, func_names, staged_tests,
            )

    sys.exit(0)


if __name__ == '__main__':
    main()
