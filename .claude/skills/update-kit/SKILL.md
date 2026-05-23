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

Use the **clone-kit** command from `commands.md`.

If `.upstream/` already exists, use the **trash** command from `commands.md` first, then re-run **clone-kit**.

If the clone fails due to authentication, stop and ask the user to run `gh auth login`.

## Step 2: Sync docs, rules, and skills

Target directories: `.claude/docs`, `.claude/rules`, `.claude/skills`.

### 2a. Enumerate upstream files

Use the **find-upstream** command from `commands.md`.

### 2b. Overwrite changed or new files

For each upstream file:

1. Derive the local path by stripping the `.upstream/` prefix (e.g. `.upstream/.claude/docs/foo.md` → `.claude/docs/foo.md`).
2. If the local file does not exist: write the upstream content to the local path using the Write tool and continue to the next file.
3. Compare content: use the **diff-upstream** command from `commands.md`.
4. If identical (exit 0): skip.
   If differs (exit 1): use the **trash** command from `commands.md` to remove the local file, then write the upstream content.

### 2c. Trash local-only files

Use the **find-local** command from `commands.md`.

For each local file, check whether the upstream counterpart exists: use the **upstream-exists** command from `commands.md`.

If absent upstream, use the **trash** command from `commands.md`.

## Step 3: Trash the upstream clone

Use the **trash** command from `commands.md`.

## Step 4: Report

Use the **kit-diff-stat** command from `commands.md`.

## Step 5: Commit

Invoke /commit.
