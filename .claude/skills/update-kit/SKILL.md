---
name: update-kit
description: Update this project's docs and skills from the latest version of reivosar/ai-developer-kit. Use this skill when the user says "update the kit", "pull the latest rules", "sync the kit", or "get the latest skills."
---

# Update Kit

Fetch the latest `.claude` contents from `reivosar/ai-developer-kit` and apply them to this project.

## Sync behaviour

- Files whose content differs from upstream are trashed then replaced.
- Files present locally but absent in upstream are trashed.
- Files identical to upstream are skipped.

## What is never touched

- `CLAUDE.md` — project-specific behavior
- `.claude/settings.json` — project-specific permissions and hooks
- `.claude/hooks/` — project-specific hook scripts

## Step 1: Clone the kit into the worktree

Clone into `.upstream/` so all subsequent commands stay within the project tree:

```bash
gh repo clone reivosar/ai-developer-kit .upstream -- --depth=1 --quiet
```

If `.upstream/` already exists, trash it first then re-clone:

```bash
.claude/hooks/trash.sh .upstream
gh repo clone reivosar/ai-developer-kit .upstream -- --depth=1 --quiet
```

If the clone fails due to authentication, stop and ask the user to run `gh auth login`.

## Step 2: Sync docs, rules, and skills

Target directories: `.claude/docs`, `.claude/rules`, `.claude/skills`.

### 2a. Enumerate upstream files

Issue all three as separate Bash tool calls in one message (parallel):

```bash
find . -path './.upstream/.claude/docs/*' -type f
```
```bash
find . -path './.upstream/.claude/rules/*' -type f
```
```bash
find . -path './.upstream/.claude/skills/*' -type f
```

### 2b. Overwrite changed or new files

For each upstream file:

1. Derive the local path by stripping the `.upstream/` prefix (e.g. `.upstream/.claude/docs/foo.md` → `.claude/docs/foo.md`).
2. If the local file does not exist: write the upstream content to the local path using the Write tool and continue to the next file.
3. Compare content:
   ```bash
   diff -q .upstream/.claude/docs/foo.md .claude/docs/foo.md
   ```
4. If `diff -q` exits 0 (identical): skip.
   If `diff -q` exits 1 (differs): trash the local file, then write the upstream content:
   ```bash
   .claude/hooks/trash.sh <local_file>
   ```

### 2c. Trash local-only files

Find local files absent from upstream — issue all three in parallel:

```bash
find . -path './.claude/docs/*' -type f
```
```bash
find . -path './.claude/rules/*' -type f
```
```bash
find . -path './.claude/skills/*' -type f
```

For each local file, check whether the corresponding upstream file exists:

```bash
test -f .upstream/<local_path>
```

If absent upstream, trash it:

```bash
.claude/hooks/trash.sh <local_file>
```

## Step 3: Trash the upstream clone

```bash
.claude/hooks/trash.sh .upstream
```

## Step 4: Report

```bash
git diff --stat .claude/docs/ .claude/rules/ .claude/skills/
git status
```

## Step 5: Commit

Invoke /commit.
