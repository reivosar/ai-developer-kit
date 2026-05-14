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
- `.claude/docs/code-style.md`
- `.claude/docs/testing.md`

Read only after confirming the domain applies:
- Implementation conventions needed (new code alongside tests) → `.claude/docs/coding.md`

## Arguments

`$ARGUMENTS` is the target file, function, or module to test. If empty, ask.

## Process

### 1. Understand the code

Read `.claude/docs/investigation-tools.md`, then use `symbol_search` to locate
the implementation. Read only the surfaced files.

Identify:
- Public interface: inputs, outputs, side effects
- Happy path
- Error / edge cases not yet covered
- Existing test patterns in the same repo

### 2. Red — write failing tests

Write tests that:
- Cover the happy path, each error case, and boundary values
- Fail now (implementation already exists, so tests that pass immediately test nothing new)
- Follow the naming and structure of existing tests

Run the test suite and confirm new tests fail or add new coverage.

### 3. Verify green

If all new tests pass without changes: report which cases were already covered
and which are newly covered. Do not declare success for tests that pass trivially.

## Report

- Tests added: file paths and what each covers
- Cases still untested: what would require refactoring or mocking to reach
