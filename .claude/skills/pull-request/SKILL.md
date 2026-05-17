---
name: pull-request
description: Create a pull request from the current feature branch. Use this skill when the user says "create a PR", "open a pull request", "PR this", "ready to merge", or has finished a coding task and the next step is to get it reviewed.
---

# Pull Request

Create a pull request from the current branch to main.

## Setup

Always read:
- `.claude/docs/git-workflow.md`
- `.claude/docs/commands.md`

## Step 1: Check state

Use the **branch-state** command from `commands.md`, plus `gh pr view --json state`.

## Step 2: Push

Use the **push** command from `commands.md`.

## Step 3: Draft title and body

Derive title and body using the rules in `git-workflow.md`. Use the **pr-create** command from `commands.md`.

## Step 4: Report

Output the PR URL.
