---
name: update-kit
description: Update this project's rule-library and skills from the latest version of reivosar/ai-developer-kit. Use this skill when the user says "update the kit", "pull the latest rules", "sync the kit", or "get the latest skills."
---

# Update Kit

Fetch the latest `.claude` contents from `reivosar/ai-developer-kit` and apply them to this project.

## What gets replaced (total replacement)

- `.claude/rule-library/` — completely replaced with upstream (local-only files are deleted)
- `.claude/rules/` — completely replaced with upstream (local-only files are deleted)
- `.claude/skills/` — completely replaced with upstream (local-only skills are deleted)

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

## Step 3: Replace rule-library, rules, and skills entirely

```bash
.claude/hooks/trash.sh .claude/rule-library
.claude/hooks/trash.sh .claude/rules
.claude/hooks/trash.sh .claude/skills
cp -r /tmp/ai-developer-kit-update/.claude/rule-library .claude/rule-library
cp -r /tmp/ai-developer-kit-update/.claude/rules .claude/rules
cp -r /tmp/ai-developer-kit-update/.claude/skills .claude/skills
```

## Step 4: Report

```bash
git diff --stat .claude/rule-library/ .claude/rules/ .claude/skills/
git status
```
