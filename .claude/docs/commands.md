# Canonical Commands

Use these exact command forms. Do not paraphrase or reconstruct from memory. Commands for syncing with the upstream kit are in `kit-update-commands.md`.

## commit

```bash
git commit -m "<type>(<scope>): <summary>" -m "<body paragraph>"
```

Give each paragraph its own `-m`. Command substitution (`$(...)`, backticks) and here-documents are blocked by the pre-bash hook, so write backticks only inside single quotes.

Type, scope, and summary follow Conventional Commits. See `git-workflow.md` for type selection and summary rules. Include a body only when the summary alone is insufficient to convey why the change was made.

## push

```bash
git push -u origin HEAD
```

Always use this form. Never `git push --force` without explicit user instruction.

## pr-create

```bash
gh pr create --title "<title>" --body-file .trash/pr-body.md
```

Write the body file first, with the Write tool, from the project's pull request template, or from `.claude/templates/github/PULL_REQUEST_TEMPLATE.md` when the project has none: keep every heading, replace each comment with the text, and delete an optional section that has nothing to say. `.trash/` is ignored by git. The pre-bash hook blocks the command when a required section is missing or empty.

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
  --body-file .trash/issue-body.md
```

Files a GitHub issue on the kit repository. Choose a label from: `rule-gap`, `skill-gap`, `new-pattern`, `enhancement`. Write the body file first from `.claude/templates/github/ISSUE_TEMPLATE/kit_feedback.md`, the same way as for **pr-create**. For an issue on the project itself, drop `--repo` and write the body from `bug_report.md` or `feature_request.md` in the same directory, or from one of the project's own issue templates.

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

Detects changed files from `git diff main...HEAD` (or staged files when `STATIC_ANALYSIS_MODE=staged`), groups by extension, and runs the appropriate linter for each group: flake8 for Python; `tsc --noEmit` and a linter for TypeScript (ESLint when the project has an ESLint configuration, Biome otherwise); `go vet` and `gofmt -l` for Go; `cargo clippy` with warnings denied for Rust. `go vet`, `tsc`, and `cargo clippy` run once in each project a file belongs to (the nearest directory above it with `go.mod`, `tsconfig.json`, or `Cargo.toml`); a Go or TypeScript file in no project is checked alone, and a Rust file in no Cargo package is reported as not checked. Every code file is held to 200 lines: by the linters, and for Rust and shell files by a line count. markdownlint, yamllint, and a JSON parse for documents and data. A missing linter is installed through `.claude/hooks/install-tool.sh` and then run; one that cannot be installed is reported as ERROR and causes non-zero exit — all applicable tools run regardless so every problem is visible in one pass. The `git commit` hook runs the same script on the staged files and blocks the commit on any finding. To add support for a new file type, extend `.claude/hooks/static-analysis.sh`.
