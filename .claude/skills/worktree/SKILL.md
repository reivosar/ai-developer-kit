---
name: worktree
description: Create a git worktree for isolated work on a new branch, or clean up a worktree after its PR is merged. Use this skill at the start of any coding task before writing any code.
---

# Worktree

Two modes: **create** a worktree at the start of a task, or **cleanup** a worktree after its PR is merged.

## Arguments

- Create: `<type>/<description>` — branch name (e.g. `feat/user-auth`)
- Cleanup: `cleanup <PR>` — PR number to check and remove (e.g. `cleanup 42`)

Valid branch types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`.

## Create

### 1. Validate

Confirm `$ARGUMENTS` matches `<type>/<description>`.
Extract `<description>` as the worktree directory name.
If the format is invalid, stop and ask the user for the correct branch name.

### 2. Create

```bash
git fetch origin
git worktree add .claude/worktrees/<description> -b <type>/<description> origin/main
```

### 3. Report

State the worktree path: `.claude/worktrees/<description>`
All subsequent work in this task must be performed inside that worktree.

## Cleanup

### 1. Check PR state

```bash
gh pr view <PR> --json state,headRefName
```

If state is not `MERGED`, stop and report the current state. Do not remove anything.

### 2. Remove

Extract `<description>` from the branch name (part after `/`).
Run the `worktree-remove` command from `commands.md`:

```bash
git worktree remove .claude/worktrees/<description>
git branch -d <type>/<description>
```

### 3. Report

Confirm the worktree and branch were removed.
