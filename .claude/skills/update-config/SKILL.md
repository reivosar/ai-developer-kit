---
name: update-config
description: Use this skill to configure the Claude Code harness via settings.json. Automated behaviors ("from now on when X", "each time X", "whenever X", "before/after X") require hooks configured in settings.json - the harness executes these, not Claude, so memory/preferences cannot fulfill them. Also use for: permissions ("allow X", "add permission", "move permission to"), env vars ("set X=Y"), hook troubleshooting, or any changes to settings.json/settings.local.json files. Examples: "allow npm commands", "add bq permission to global settings", "move permission to user settings", "set DEBUG=true", "when claude stops show X". For simple settings like theme/model, suggest the /config command.
---

# Update Config Skill

Modify Claude Code configuration by updating settings.json files.

## When Hooks Are Required (Not Memory)

If the user wants something to happen automatically in response to an EVENT, they need a **hook** configured in settings.json. Memory/preferences cannot trigger automated actions.

**These require hooks:**
- "Before compacting, ask me what to preserve" → PreCompact hook
- "After writing files, run prettier" → PostToolUse hook with Write|Edit matcher
- "When I run bash commands, log them" → PreToolUse hook with Bash matcher
- "Always run tests after code changes" → PostToolUse hook

**Hook events:** PreToolUse, PostToolUse, PreCompact, PostCompact, Stop, Notification, SessionStart

## CRITICAL: Read Before Write

**Always read the existing settings file before making changes.** Merge new settings with existing ones — never replace the entire file.

## CRITICAL: Use AskUserQuestion for Ambiguity

When the user's request is ambiguous, use AskUserQuestion to clarify:
- Which settings file to modify (user/project/local)
- Whether to add to existing arrays or replace them
- Specific values when multiple options exist

## Decision: /config command vs Direct Edit

**Suggest the `/config` slash command** for these simple settings (do NOT invoke /coding for these):
- `theme`, `editorMode`, `verbose`, `model`
- `language`, `alwaysThinkingEnabled`
- `permissions.defaultMode`

**Invoke /coding** for everything else:
- Hooks (PreToolUse, PostToolUse, etc.)
- Permission rules (allow/deny arrays)
- Environment variables
- MCP server configuration

## Workflow

### 1. Clarify intent

Ask if the request is ambiguous (which file, what scope).

### 2. Read and plan

Read the target settings file. Determine exactly what to add/change/remove and which test cases cover the new behavior.

For permission allow/deny changes, identify the test file (e.g., `test_allow_list.py`) and the test cases that must be added.

### 3. Delegate to /coding

Pass a concrete spec to `/coding` that includes:

```
Modify <settings_file_path> to <change_description>.

Files to change:
- <settings_file_path>
- <test_file_path> (add test cases before changing settings)

Test cases to add first (Red phase):
- ("<new_allowed_command>", False)   -- allowed
- ("<edge_case_blocked>",  True)    -- still blocked

Then implement:
- Add "<Bash(pattern)>" to permissions.allow in <settings_file_path>
```

`/coding` enforces Red-Green-Refactor, so tests must be written and confirmed failing before the settings change is made.

**Exception:** If the project has no test harness for settings (no test_allow_list.py or equivalent), note this and implement directly — but document the gap via `/feedback`.

### 4. Confirm

Tell the user what was changed and in which file.

## Settings File Locations

| File | Scope | Git | Use For |
|------|-------|-----|---------|
| `~/.claude/settings.json` | Global | N/A | Personal preferences for all projects |
| `.claude/settings.json` | Project | Commit | Team-wide hooks, permissions, plugins |
| `.claude/settings.local.json` | Project | Gitignore | Personal overrides for this project |

Settings load in order: user → project → local (later overrides earlier).

## Merging Arrays

When adding to permission arrays or hook arrays, **merge with existing**, don't replace:

```json
{
  "permissions": {
    "allow": [
      "Bash(git *)",      // existing
      "Bash(npm *)"       // new
    ]
  }
}
```
