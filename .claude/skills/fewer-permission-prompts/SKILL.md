---
name: fewer-permission-prompts
description: Allowlist a safe bash command to stop Claude Code from prompting for
  permission every time it runs. Use when the user says "stop asking me about X",
  "always allow X", "add X to the allowlist", or "fewer prompts for Y."
---

# Fewer Permission Prompts

Add a bash command pattern to `permissions.allow` in `.claude/settings.json`
so it runs without a permission prompt.

## Arguments

`$ARGUMENTS` is the command or pattern to allow (e.g. "npm run dev",
"python3 scripts/", "gh workflow run").

## Process

This skill delegates to `/edit-kit`, which delegates to `/coding` for TDD.

### 1. Identify the pattern

From $ARGUMENTS, derive a Bash allow pattern:
- Exact command: `"Bash(npm run dev)"`
- Wildcard suffix: `"Bash(npm run dev*)"`
- Keep patterns as specific as possible — broad patterns (e.g. `Bash(*)`) defeat the purpose

### 2. Check for conflicts

Read `.claude/settings.json`. Confirm:
- The pattern is not already in `permissions.allow`
- It is not blocked by `permissions.deny`

If already present, report and stop.

### 3. Add via /edit-kit

Invoke `/edit-kit` with:
```
Add "Bash(<pattern>)" to permissions.allow in .claude/settings.json.
Test case to add to test_allow_list.py first:
  ('<exact_example_command>', False)  -- should be allowed after change
```

### 4. Confirm

Report the pattern added and which settings file was modified.
