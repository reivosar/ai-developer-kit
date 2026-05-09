---
name: update-kit
description: Update this project's rule-library and skills from the latest version of reivosar/ai-developer-kit. Use this skill when the user says "update the kit", "pull the latest rules", "sync the kit", or "get the latest skills."
---

# Update Kit

Fetch the latest rule-library and skills from `reivosar/ai-developer-kit` and apply them to this project.

## What gets updated

- `.claude/rule-library/*.md` — all rule files (overwritten)
- `.claude/skills/*/SKILL.md` — each skill's definition (overwritten)

## What is never touched

- `CLAUDE.md` — project-specific behavior
- `.claude/settings.json` — project-specific permissions and hooks
- `.claude/hooks/` — project-specific hook scripts
- Any file not present in the kit (project-added files are preserved)

## Step 1: Check prerequisites

```bash
gh auth status
```

If not authenticated, stop and ask the user to run `gh auth login`.

## Step 2: Clone the kit to a fixed temp path

Clean up any previous clone, then clone fresh:

```bash
.claude/hooks/trash.sh /tmp/ai-developer-kit-update
gh repo clone reivosar/ai-developer-kit /tmp/ai-developer-kit-update -- --depth=1 --quiet
```

## Step 3: Update rule-library

List upstream rule files:

```bash
ls /tmp/ai-developer-kit-update/.claude/rule-library/
```

For each `.md` file listed:
- Read `/tmp/ai-developer-kit-update/.claude/rule-library/<file>.md` to get upstream content
- If `.claude/rule-library/<file>.md` exists locally → **Edit** (replace full content)
- If it does not exist → **Write** (create new file)

## Step 4: Update skills

List upstream skill directories:

```bash
ls /tmp/ai-developer-kit-update/.claude/skills/
```

For each skill directory listed:
- Read `/tmp/ai-developer-kit-update/.claude/skills/<name>/SKILL.md` to get upstream content
- If `.claude/skills/<name>/SKILL.md` exists locally → **Edit** (replace full content)
- If it does not exist → **Write** (create new file; Write creates parent directories automatically)

## Step 5: Clean up

```bash
.claude/hooks/trash.sh /tmp/ai-developer-kit-update
```

## Step 6: Report

Show what changed:

```bash
git diff --stat .claude/rule-library/ .claude/skills/
```

List any new files added (skills or rules not previously in the project):

```bash
git status
```
