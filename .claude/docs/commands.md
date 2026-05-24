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

## clone-kit

```bash
gh repo clone reivosar/ai-developer-kit .upstream -- --depth=1 --quiet
```

Clones the upstream kit into `.upstream/` inside the project tree. Never run from inside an existing worktree.

## trash

```bash
.claude/hooks/trash.sh <path>
```

Moves `<path>` to `.trash/<timestamp>/`. Always use this instead of `rm`.

## find-upstream

```bash
find . -path './.upstream/.claude/docs/*' -type f
find . -path './.upstream/.claude/rules/*' -type f
find . -path './.upstream/.claude/skills/*' -type f
find . -path './.upstream/.claude/hooks/*' -type f
```

Issue all four as a parallel batch. Enumerates all files in the upstream clone.

## find-local

```bash
find . -path './.claude/docs/*' -type f
find . -path './.claude/rules/*' -type f
find . -path './.claude/skills/*' -type f
find . -path './.claude/hooks/*' -type f
```

Issue all four as a parallel batch. Enumerates all local kit files.

## diff-upstream

```bash
diff -q .upstream/<path> <local_path>
```

Compares an upstream file against its local counterpart. Exit 0 = identical; exit 1 = differs.

## upstream-exists

```bash
test -f .upstream/<local_path>
```

Returns exit 0 if the upstream counterpart of a local file exists; exit 1 if absent.

## kit-diff-stat

```bash
git diff --stat .claude/docs/ .claude/rules/ .claude/skills/ .claude/hooks/
git status
```

Run as a parallel batch. Shows the summary of all kit file changes before committing.

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
