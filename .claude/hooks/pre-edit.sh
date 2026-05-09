#!/usr/bin/env bash
# PreToolUse hook for Write/Edit — enforces TDD Red phase.
# Blocks editing implementation files when no test changes are staged or in the last commit.
# Receives JSON on stdin: {"tool_name": "...", "tool_input": {"file_path": "..."}}

set -euo pipefail

INPUT=$(cat)

FILE=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null || true)

[[ -z "$FILE" ]] && exit 0

# Skip kit infrastructure — rules, skills, hooks, config, docs
case "$FILE" in
  .claude/*|*.md|*.json|*.yaml|*.yml|*.toml|*.ini|*.sh|*.env*|*.txt|*.lock|*.sum|Makefile|Dockerfile*)
    exit 0 ;;
esac

# Skip test files themselves (you must be able to write tests)
BASENAME=$(basename "$FILE")
if echo "$BASENAME" | grep -qiE '(test|spec)(\.|_|$)'; then
  exit 0
fi
if echo "$FILE" | grep -qiE '(/__tests__/|/tests?/|/specs?/)'; then
  exit 0
fi

# Only enforce on implementation source code
case "$FILE" in
  *.ts|*.tsx|*.js|*.jsx|*.mts|*.mjs|\
  *.py|\
  *.go|\
  *.java|\
  *.rb|\
  *.rs|\
  *.kt|*.kts|\
  *.swift|\
  *.cs|\
  *.cpp|*.cc|*.cxx|*.c|*.h|*.hpp|\
  *.php)
    : ;;
  *)
    exit 0 ;;
esac

TEST_PATTERN='(test|spec)(\.|_|-|/)'

# 1. Tests staged right now
STAGED=$(git diff --staged --name-only 2>/dev/null || true)
if echo "$STAGED" | grep -qiE "$TEST_PATTERN"; then
  exit 0
fi

# 2. Tests in the most recent commit (Red phase completed, now writing Green)
LAST_COMMIT=$(git log -1 --name-only --pretty=format: 2>/dev/null || true)
if echo "$LAST_COMMIT" | grep -qiE "$TEST_PATTERN"; then
  exit 0
fi

echo "BLOCKED: Red phase required. Write a failing test before editing implementation." >&2
echo "  File: $FILE" >&2
echo "  Stage a test file first, then run tests to confirm they fail, then implement." >&2
exit 2
