---
name: troubleshooting
description: Investigate and resolve broken behavior. The defining condition is uncertainty about the cause — something is wrong but why is unknown. Use this skill when the user shares an error message, stack trace, failing test, or unexpected behavior, or says "this is broken", "it's not working", "help me debug this." Do NOT use the coding skill for this — diagnosis must come before any fix.
---

# Troubleshooting

Start from broken behavior with unknown cause. Diagnose first — do not write any fix until the root cause is stated. Change only what the root cause requires.

## Setup

Read before proceeding:
- `.claude/docs/git-workflow.md`
- `.claude/docs/code-style.md`

Read only after investigation confirms the domain:
- Bug is in test code or test setup → `.claude/docs/testing.md`
- Bug involves auth, input handling, or a security boundary → `.claude/docs/security.md`

Do not read testing.md or security.md speculatively before you know the bug's domain.

## Arguments

The problem description or error message is passed as `$ARGUMENTS`. If the user pasted it inline, use that. If they mentioned a file, read it first.

## Process

### 0. Worktree setup

If not already inside a worktree, invoke /worktree with a branch name in `<type>/<description>` format.
All implementation work must happen inside the worktree — never in the main working directory.

### 1. Investigate (read only)

Before touching anything, understand the system:

- Read `.claude/docs/investigation-tools.md`, then use `symbol_search` to search for the error string or failing symbol
- Trace the call path from the entry point to where the error occurs
- Check git history using `history_search` to find when the behavior changed — then `git show <hash>` on specific commits; never use `git log -p` which dumps full file diffs for every match

Resist the urge to fix immediately. The first obvious explanation is often wrong.

### 2. Form a hypothesis

State the root cause in one sentence before writing any code. If there are multiple plausible causes, rank them and check the most likely one first.

## Report

State the root cause, the required fix, and any other occurrences of the same pattern found during investigation.

### 3. Fix

Invoke /coding with the root cause statement and fix description. /coding handles implementation, review, commit, and PR.

If the task was investigation only and no files need to change, stop here.
