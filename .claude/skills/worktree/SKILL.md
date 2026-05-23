---
name: worktree
description: Create an isolated git worktree before starting any task that modifies files. Use this skill as the first step of every implementation task, and also when the user wants parallel work, says "I need to switch context", "can we work on this in parallel", or asks Claude to work on something in the background.
---

# Worktree

## Setup

Always read:
- `.claude/docs/git-workflow.md`
- `.claude/docs/commands.md`

## Arguments

`$ARGUMENTS` is the branch name in `<type>/<description>` format.
If omitted, ask the user for a branch name.

The worktree directory name (`<name>`) is the description part of the branch name.

## Pre-flight: verify CWD is the project root

Use the **worktree-list** command from `commands.md` and note the first line — that is the main worktree path.

If the current working directory is NOT the main worktree path, stop and navigate there first:

```bash
cd <main-worktree-path>
```

Never create a worktree from inside an existing worktree. Nested worktrees break git state and cause commits to land on the wrong branch.

## Create

Use the **worktree-add** command from `commands.md`.

## Manage

- List: use the **worktree-list** command from `commands.md`.
- Remove: use the **worktree-remove** command from `commands.md`.
