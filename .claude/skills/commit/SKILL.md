---
name: commit
description: Create a well-formed git commit for staged changes using Conventional Commits format. Use this skill when the user asks to commit, says "commit this", "make a commit", or "save my changes." Also use it at the end of a task when changes are ready to be committed.
---

# Commit

Create a Conventional Commits message for what is staged and commit it.

## Setup

Read before proceeding:
- `.claude/docs/git-workflow.md`
- `.claude/docs/diff-strategy.md`

## Step 1: Check branch and staged changes

```bash
git status
git diff --staged --stat
```

Apply the threshold from `.claude/docs/diff-strategy.md` to the stat summary line:
- Under threshold: `git diff --staged`
- Over threshold: `git diff --staged --name-only`, then `git diff --staged -- <file>` for every file

Read all files — do not skip any based on perceived importance.

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
