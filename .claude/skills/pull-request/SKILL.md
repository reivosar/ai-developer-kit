---
name: pull-request
description: Create a pull request from the current feature branch. Use this skill when the user says "create a PR", "open a pull request", "PR this", "ready to merge", or has finished a coding task and the next step is to get it reviewed.
---

# Pull Request

Create a pull request from the current branch to main.

## Setup

Read `.claude/docs/git-workflow.md` before proceeding.

## Step 1: Check state

```bash
git status
git fetch origin
git log origin/main...HEAD --oneline
gh pr view --json state
```

## Step 2: Push

```bash
git push -u origin HEAD
```

## Step 3: Draft title and body

Derive title from the commit log (single commit: use subject; multiple commits: summarize). See `.claude/docs/git-workflow.md` for title rules and body structure.

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

## Step 4: Report

Output the PR URL.
