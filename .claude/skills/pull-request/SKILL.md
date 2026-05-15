---
name: pull-request
description: Create a pull request from the current feature branch. Use this skill when the user says "create a PR", "open a pull request", "PR this", "ready to merge", or has finished a coding task and the next step is to get it reviewed.
---

# Pull Request

Create a pull request from the current branch to main.

## Setup

Read `.claude/docs/git-workflow.md` before proceeding.

## Step 1: Verify branch state

Run in a single parallel batch:
```bash
git status
git fetch origin
git log origin/main...HEAD --oneline
```

Guards:
- If `git status` shows `On branch main` — stop. Tell the user to create a feature branch first.
- If there are unstaged changes — run the `commit` skill first, then return here.
- If there are no commits ahead of `origin/main` — stop. Nothing to PR.

Check if the current branch already has a merged PR:

```bash
gh pr view --json state 2>/dev/null
```

If `state` is `MERGED`, the branch was already merged. Create a new branch from the current HEAD before opening a PR:

```bash
git checkout -b <type>/<new-description>
```

Derive the new branch name from the unreleased commits. Then continue to Step 2 from the new branch.

## Step 2: Push the branch

```bash
git push -u origin HEAD
```

If the push fails due to diverged history, do not force push. Report the conflict to the user.

## Step 3: Draft the PR

**Title** — derive from the commit log:
- Single commit: use the commit subject line as-is
- Multiple commits: write a one-line summary of what the set of commits achieves as a whole

Title rules (same as commit summary):
- Imperative mood
- Under 72 characters
- No period at the end

**Body** — use this template:

```
## What

<1–3 bullets describing what changed>

## Why

<The motivation: what problem this solves or what requirement it fulfills>

## How to test

<Concrete steps a reviewer can follow to verify the change works>
```

## Step 4: Create the PR

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## What

<bullets>

## Why

<motivation>

## How to test

<steps>
EOF
)"
```

## Step 5: Report

Output the PR URL so the user can share or open it.

## Step 6: Post-merge cleanup

After the PR is merged on GitHub, remove the worktree and delete the local branch:

```bash
git worktree remove .claude/worktrees/<name>
git branch -d <type>/<description>
```

`<name>` is the description part of the branch name (e.g. for `feat/user-auth`, `<name>` is `user-auth`).
