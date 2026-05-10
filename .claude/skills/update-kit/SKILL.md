---
name: update-kit
description: Update this project's docs and skills from the latest version of reivosar/ai-developer-kit. Use this skill when the user says "update the kit", "pull the latest rules", "sync the kit", or "get the latest skills."
---

# Update Kit

Fetch the latest `.claude` contents from `reivosar/ai-developer-kit` and apply them to this project.

## Sync behaviour

- Files whose size or mtime differ from upstream are overwritten.
- Files present locally but absent in upstream are trashed.
- Files identical to upstream are skipped.

## What is never touched

- `CLAUDE.md` — project-specific behavior
- `.claude/settings.json` — project-specific permissions and hooks
- `.claude/hooks/` — project-specific hook scripts

## Step 1: Check prerequisites

```bash
gh auth status
```

If not authenticated, stop and ask the user to run `gh auth login`.

## Step 2: Clone the kit to a fixed temp path

```bash
gh repo clone reivosar/ai-developer-kit /tmp/ai-developer-kit-update -- --depth=1 --quiet
```

If the clone fails because the directory already exists, proceed using the existing files.

## Step 3: Sync docs, rules, and skills

Target directories: `.claude/docs`, `.claude/rules`, `.claude/skills`.

### 3a. Overwrite changed or new files

Enumerate every file in the upstream clone — issue all three as separate Bash tool calls in one message (parallel):

```bash
cd /tmp/ai-developer-kit-update && find . -path './.claude/docs/*' -type f
```
```bash
cd /tmp/ai-developer-kit-update && find . -path './.claude/rules/*' -type f
```
```bash
cd /tmp/ai-developer-kit-update && find . -path './.claude/skills/*' -type f
```

For each upstream file:

1. Derive the local path by stripping the `/tmp/ai-developer-kit-update/` prefix.
2. Compare size and mtime:
   ```bash
   stat -f "%z %m" <upstream_file>
   stat -f "%z %m" <local_file> 2>/dev/null
   ```
3. If the local file does not exist, or size/mtime differ: read the upstream file content and write it to the local path using the Write tool.
4. If size and mtime are identical: skip the file.

### 3b. Trash local-only files

Find local files absent from upstream — issue all three as separate Bash tool calls in one message (parallel):

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
test -f /tmp/ai-developer-kit-update/<local_path>
```

If not found upstream, trash it:

```bash
.claude/hooks/trash.sh <local_file>
```

## Step 4: Report

```bash
git diff --stat .claude/docs/ .claude/rules/ .claude/skills/
git status
```
