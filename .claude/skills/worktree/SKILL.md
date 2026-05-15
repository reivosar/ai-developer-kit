---
name: worktree
description: Create an isolated git worktree before starting any task that modifies files. Use this skill as the first step of every implementation task, and also when the user wants parallel work, says "I need to switch context", "can we work on this in parallel", or asks Claude to work on something in the background.
---

# Worktree

Create an isolated git worktree. This is the **mandatory first step** for any task that modifies files — all implementation work must happen inside a worktree, never in the main working directory.

## Setup

Read `.claude/docs/git-workflow.md` before proceeding.

## Arguments

`$ARGUMENTS` is the branch name in `<type>/<description>` format (e.g. `feat/user-auth`, `fix/login-bug`).
If omitted, ask the user: "What branch name should I use? (e.g. feat/..., fix/..., refactor/...)"

The worktree directory name (`<name>`) is derived from the description part of the branch name.

## Create the worktree

```bash
git fetch origin
git worktree add .claude/worktrees/<name> -b <type>/<description> origin/main
```

This creates `.claude/worktrees/<name>/` on a new branch `<type>/<description>`, forked from `origin/main`.

## When to use worktrees

- **Standard implementation**: the first step of every task that writes or modifies files — before any other work begins
- **Bug fix during a feature**: you're mid-feature but a critical bug needs fixing now — open a worktree for the fix, keep the feature branch clean
- **Parallel review**: one session writes code, another reviews it with a fresh context (no anchoring bias from having written it)
- **Risky experiment**: try a big refactor in a worktree; discard it cleanly if it doesn't work out
- **Subagent isolation**: give subagents their own working copy so they don't step on each other (set `isolation: worktree` in agent frontmatter)

## Copy gitignored files

New worktrees are clean checkouts — `.env` and similar files won't be there. To copy them automatically, add a `.worktreeinclude` at the project root:

```
.env
.env.local
config/local.json
```

## Cleanup behavior

| Situation | Result |
|---|---|
| Worktree closed with no changes | Branch and directory deleted automatically |
| Worktree closed with changes | Prompt to keep or delete |
| Subagent worktree, no changes | Deleted automatically |

## Manual management

```bash
git worktree list
git worktree remove .claude/worktrees/<name>
```

Add `.claude/worktrees/` to `.gitignore` so worktree contents don't show as untracked files in the main repo.
