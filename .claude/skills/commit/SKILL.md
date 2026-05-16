---
name: commit
description: Create a well-formed git commit for staged changes using Conventional Commits format. Use this skill when the user asks to commit, says "commit this", "make a commit", or "save my changes." Also use it at the end of a task when changes are ready to be committed.
---

# Commit

Create a Conventional Commits message for what is staged and commit it.

## Setup

Read `.claude/docs/git-workflow.md` before proceeding.

## Step 1: Verify branch and staged changes

Run in a single parallel batch:
```bash
git status
git diff --staged
```

From `git status`:
- If on `main`: STOP. Never commit directly to main. Branch first:
  ```bash
  git pull
  git checkout -b <type>/<short-description>
  ```
  Then return to commit.
- If on a branch unrelated to this task: STOP. Go back to main and cut a proper branch for this task.

From `git diff --staged`:
Read the diff carefully. The commit message should reflect the *intent* of the change, not just list files modified.

## Step 2: Draft the message

Format, type selection, summary rules, and body guidance: see `.claude/docs/git-workflow.md`.

## Step 3: Propose and confirm

Show the proposed message to the user and wait for approval or edits before committing. Do not stage unstaged files unless explicitly asked.

## Step 4: Commit

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <summary>

<body if any>
EOF
)"
```

## Step 5: Create PR

After a successful commit on a feature branch, immediately invoke the pull-request skill.
Do not wait for the user to ask.
