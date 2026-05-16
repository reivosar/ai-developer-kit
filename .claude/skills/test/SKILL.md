---
name: test
description: Generate tests or improve test coverage for existing code. Use when
  the user says "write tests", "add tests", "test this", "improve coverage", or
  "what's not tested here?"
---

# Test

Write tests for existing code. Follow Red-Green-Refactor.

## Setup

Always read:
- `.claude/docs/git-workflow.md`
- `.claude/docs/code-style.md`
- `.claude/docs/testing.md`

Read only after confirming the domain applies:
- Implementation conventions needed (new code alongside tests) → `.claude/docs/coding.md`

## Arguments

`$ARGUMENTS` is the target file, function, or module to test. If empty, ask.

## Process

### 0. Worktree setup

If not already inside a worktree, invoke /worktree with a branch name in `<type>/<description>` format.
All implementation work must happen inside the worktree — never in the main working directory.

### 1. Understand the code

Read `.claude/docs/investigation-tools.md`, then use `symbol_search` to locate
the implementation. Read only the surfaced files.

Identify:
- Public interface: inputs, outputs, side effects
- Happy path
- Error / edge cases not yet covered
- Existing test patterns in the same repo

## Report

List: cases to cover (happy path, error paths, boundary values), existing test patterns to follow, and cases that would require refactoring or mocking to reach.

### 2. Implement

Invoke /coding with the test requirements from Step 1 and the Report above. /coding handles writing the tests, review, commit, and PR.
