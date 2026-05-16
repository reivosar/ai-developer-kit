---
name: worktree
description: Create an isolated git worktree before starting any task that modifies files. Use this skill as the first step of every implementation task, and also when the user wants parallel work, says "I need to switch context", "can we work on this in parallel", or asks Claude to work on something in the background.
---

# Worktree

## Setup

Read `.claude/docs/git-workflow.md` before proceeding.

## Arguments

`$ARGUMENTS` is the branch name in `<type>/<description>` format.
If omitted, ask the user for a branch name.

The worktree directory name (`<name>`) is the description part of the branch name.

## Create

```bash
git fetch origin
git worktree add .claude/worktrees/<name> -b <type>/<description> origin/main
```

## Manage

```bash
git worktree list
git worktree remove .claude/worktrees/<name>
git branch -d <type>/<description>
```
