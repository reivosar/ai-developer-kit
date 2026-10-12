# Canonical Commands

Use these exact command forms. Do not paraphrase or reconstruct from memory. Commands for syncing with the upstream kit are in `kit-update-commands.md`.

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

Run as a parallel batch. If checking for an existing PR, add `gh pr view --json state` to the batch.

## diff-branch

```bash
git diff --stat main...HEAD
git log main...HEAD --oneline
```

Run as a parallel batch. Gives a size overview of the current branch vs main.

## diff-branch-files

Full branch diff. Apply the threshold from `diff-strategy.md` to the stat summary from **diff-branch**:
- Under threshold: `git diff main...HEAD`
- Over threshold: `git diff --name-only main...HEAD`, then `git diff main...HEAD -- <file>` for every file

## diff-staged

```bash
git status
git diff --staged --stat
```

Run as a parallel batch. Gives a size overview of what is staged.

## diff-staged-files

Full staged diff. Apply the threshold from `diff-strategy.md` to the stat summary from **diff-staged**:
- Under threshold: `git diff --staged`
- Over threshold: `git diff --staged --name-only`, then `git diff --staged -- <file>` for every file

## pr-diff

```bash
gh pr view $PR
gh pr diff $PR --name-only
```

Run as a parallel batch. Replace `$PR` with the PR number. Gives an overview of the PR and the list of changed files.

## pr-diff-files

Full PR diff. Apply the threshold from `diff-strategy.md`:
- Get line count: `gh pr diff $PR --stat` (read the summary line)
- Under threshold: `gh pr diff $PR`
- Over threshold: `gh pr diff $PR -- <file>` for every file

## trash

```bash
.claude/hooks/trash.sh <path>
```

Moves `<path>` to `.trash/<timestamp>/`. Always use this instead of `rm`.

## worktree-list

```bash
git worktree list
```

Lists all worktrees with their paths and current branches.

## worktree-remove

```bash
git worktree remove .claude/worktrees/<name>
git branch -d <type>/<description>
```

Removes the worktree and deletes its branch. Run sequentially.

## issue-create

```bash
gh issue create \
  --repo reivosar/ai-developer-kit \
  --title "<title>" \
  --label "<label>" \
  --body "$(cat <<'EOF'
## Insight

<What was missing or should be improved>

## Context

Project: <project name or path>
Task: <what was being worked on when this was noticed>

## Suggested change

<Which file to change and what to add or modify — leave blank if unknown>
EOF
)"
```

Files a GitHub issue on the kit repository. Choose a label from: `rule-gap`, `skill-gap`, `new-pattern`, `enhancement`.

## find-docs

```bash
find . -name "*.md" -not -path "*/.git/*"
```

Finds all markdown files in the project tree, excluding `.git/`.

## cd-worktree-root

```bash
cd <main-worktree-path>
```

Navigate to the main worktree root. Use the path shown on the first line of **worktree-list** output.

## static-analysis

```bash
.claude/hooks/static-analysis.sh
```

Detects changed files from `git diff main...HEAD` (or staged files when `STATIC_ANALYSIS_MODE=staged`), groups by extension, and runs the appropriate linter for each group. A missing linter is installed through `.claude/hooks/install-tool.sh` and then run; one that cannot be installed is reported as ERROR and causes non-zero exit — all applicable tools run regardless so every problem is visible in one pass. To add support for a new file type, extend `.claude/hooks/static-analysis.sh`.
