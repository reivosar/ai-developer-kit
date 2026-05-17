---
name: simplify
description: Review code for simplification, quality, or refactoring needs. Use
  when the user says "simplify", "clean up", "reduce complexity", "refactor for
  readability", "review this code", or "what can be improved here?"
---

# Simplify

Review code and identify concrete simplification opportunities. Do not rewrite
unless the user approves.

## Setup

Always read:
- `.claude/docs/code-style.md`

Read only when:
- Code has tests or test coverage concerns → `.claude/docs/testing.md`

## Arguments

`$ARGUMENTS` is the target: a file path, function name, or inline description.
If empty, ask the user what to review.

If `--auto` is included in arguments (e.g. `/simplify --auto src/foo.py`): skip Step 3's user confirmation.
Implement all must-fix and should-fix items directly, then return. Do not invoke /coding.

## Process

### 1. Read the target

Invoke /investigate to locate the code.

### 2. Identify issues

Look for, in priority order:
- Duplication that should be extracted
- Dead code (unreachable, unused, commented-out)
- Functions doing more than one thing
- Names that require a comment to understand
- Abstraction that obscures rather than clarifies
- Unnecessary complexity: nested conditions that can be flattened, early returns
  that replace deep nesting

Do NOT flag style preferences covered by the formatter (indentation, quotes).

### 3. Report

For each finding, give: file:line, the problem, and a concrete fix.

Group by severity:
- **Must fix** — logic is wrong, dead code is misleading, or name actively harms readability
- **Should fix** — duplication or single-responsibility violation
- **Consider** — minor clarity improvements

End with a count: "N issues found (X must, Y should, Z consider)."

If `--auto` was passed: skip the confirmation below and proceed directly to Step 4.
Otherwise ask: "Implement all / must-fix only / specific items?"

### 4. Implement

**Without `--auto`**: invoke /coding with the approved changes. /coding handles implementation, review, commit, and PR.

**With `--auto`**: implement all must-fix and should-fix items directly without invoking /coding. Return when done.
