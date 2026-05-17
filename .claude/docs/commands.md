# Canonical Commands

Use these exact command forms. Do not paraphrase or reconstruct from memory.

## commit

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <summary>

<body>
EOF
)"
```

Type, scope, and summary follow Conventional Commits. See `git-workflow.md` for type selection and summary rules. Include a body only when the summary alone is insufficient to convey why the change was made.

## push

```bash
git push -u origin HEAD
```

Always use this form. Never `git push --force` without explicit user instruction.

## pr-create

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## What

<1-3 bullets describing what changed>

## Why

<motivation — what problem this solves or what requirement it fulfills>

## How to test

<concrete steps a reviewer can follow to verify the change works>
EOF
)"
```

Title rules: imperative mood, under 72 characters, no trailing period. Derive from commit log (single commit: use subject line; multiple commits: summarize what the set achieves).

## worktree-add

```bash
git fetch origin
git worktree add .claude/worktrees/<name> -b <type>/<description> origin/main
```

`<name>` is the description part of the branch name (e.g. `feat/user-auth` → `user-auth`). Never run this from inside an existing worktree.

## branch-state

```bash
git status
git fetch origin
git log origin/main...HEAD --oneline
```

Run as a parallel batch. If checking for an existing PR, add `gh pr view --json state 2>/dev/null` to the batch.
