---
name: commit
description: Create a well-formed git commit for staged changes using Conventional Commits format. Use this skill when the user asks to commit, says "commit this", "make a commit", or "save my changes." Also use it at the end of a task when changes are ready to be committed.
---

# Commit

Create a Conventional Commits message for what is staged and commit it.

## Setup

Read `.claude/docs/git-workflow.md` before proceeding.

## Step 1: Check branch and staged changes

```bash
git status
git diff --staged --stat
```

If drafting the commit message requires understanding specific changes beyond the stat summary, also run `git diff --staged`.

## Step 2: Draft the message

See `.claude/docs/git-workflow.md` for format, type selection, and summary rules.

## Step 3: Propose and commit

Show the proposed message to the user. On confirmation:

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <summary>

<body if any>
EOF
)"
```

## Step 4: Open PR

Invoke /pull-request.
