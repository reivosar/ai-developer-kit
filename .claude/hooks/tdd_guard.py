#!/usr/bin/env python3
"""TDD guard: block an implementation change that has no test staged."""
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_lib  # noqa: E402
from function_definitions import find_definitions  # noqa: E402

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


def is_test_file(path: str) -> bool:
    return bool(_TEST_NAME_RE.search(os.path.basename(path)) or _TEST_DIR_RE.search(path))


def _is_impl_file(path: str) -> bool:
    basename = os.path.basename(path)
    if basename in _SKIP_BASENAMES:
        return False
    if path.startswith('CLAUDE'):
        return False
    _, ext = os.path.splitext(path)
    if ext.lower() in _SKIP_EXT or not ext or path.startswith('.env'):
        return False
    if is_test_file(path):
        return False
    return ext.lower() in _IMPL_EXTS


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


def _normalized(name: str) -> str:
    return name.lower().replace('-', '_')


def _module_has_test(test_paths: list[str], file_path: str) -> bool:
    # A test covers a module when it is named after it or names its file.
    basename = os.path.basename(file_path)
    stem = _normalized(re.sub(r'\.\w+$', '', basename))
    test_names = [_normalized(os.path.basename(t)) for t in test_paths]
    if any(stem in test_name for test_name in test_names):
        return True
    return _test_covers_funcs(test_paths, {basename})


def _public_names(definitions: dict) -> set[str]:
    # A private helper is tested through the public function that calls
    # it, so tests do not name it; the module's own test must be staged.
    return {name for name in definitions if not name.startswith('_')}


def _is_upstream_sync(code: str, file_path: str) -> bool:
    # /update-kit writes kit files verbatim from the clone in .upstream/;
    # copying a file is not authoring it, so no test is demanded.
    target = Path(file_path).resolve()
    for ancestor in target.parents:
        upstream = ancestor / '.upstream' / target.relative_to(ancestor)
        if upstream.is_file():
            return upstream.read_text(errors='replace') == code
    return False


def _is_checked(code: str, file_path: str) -> bool:
    if os.environ.get('TDD_GUARD_DISABLE'):
        return False
    if not code or not _is_impl_file(file_path):
        return False
    return not _is_upstream_sync(code, file_path)


def check(code: str, file_path: str) -> None:
    if not _is_checked(code, file_path):
        return
    func_names = _public_names(find_definitions(code, file_path))
    staged = [f for f in _git_files(['git', 'diff', '--staged', '--name-only']) if is_test_file(f)]
    last = [f for f in _git_files(['git', 'log', '-1', '--name-only', '--pretty=format:']) if is_test_file(f)]
    all_tests = staged + last
    if not all_tests:
        _fail("No test files staged.", file_path, func_names, staged)
    if func_names:
        if not _test_covers_funcs(all_tests, func_names):
            _fail("Staged tests do not reference the modified functions.", file_path, func_names, staged)
    else:
        if not _module_has_test(all_tests, file_path):
            _fail(f"No test for '{os.path.basename(file_path)}' found.", file_path, func_names, staged)
