# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# AI Developer Kit

Template kit for Claude Code-powered development workflows.

## Tests

Run each test suite:

```bash
python3 .claude/hooks/test_allow_list.py
python3 .claude/hooks/test_pre_edit_check.py
python3 .claude/hooks/test_pre_worktree_check.py
python3 .claude/hooks/test_hook_lib.py
```

When adding a new allowed or denied Bash command, write a failing test in `test_allow_list.py` first, then update `settings.json`.

## Architecture

This kit is Claude Code configuration only — no application code. Everything lives under `.claude/`:

### Rules (auto-loaded)

`.claude/rules/*.md` — loaded into every conversation automatically. Four files: `behavior.md`, `context-efficiency.md`, `skill-dispatch.md`, `completion-standards.md`.

### Rule library (on-demand)

`.claude/docs/*.md` — topic-specific rules (backend, security, testing, etc.). Not auto-loaded. Each skill reads only the files it needs. Once read in a session, treat as cached.

### Skills

`.claude/skills/<name>/SKILL.md` — step-by-step workflows Claude follows when a skill is invoked (e.g. `/commit`, `/update-kit`). Skills are the primary extension point of the kit.

### Hooks

`.claude/hooks/` — Python and bash scripts wired into Claude Code hook events:

- `pre-bash-check.py` — enforces the allow/deny list in `settings.json` before every Bash command
- `pre-commit.sh` — blocks commits containing secrets, invalid branch names, or trailing whitespace
- `pre-edit-check.py` / `pre-write-check.py` — guard file writes and edits
- `post-edit.sh` — runs after file edits
- `trash.sh` — moves files to `.trash/<timestamp>/`; always use this instead of `rm`

### Settings

`.claude/settings.json` — two concerns:

1. `permissions.allow` / `permissions.deny` — Bash command patterns checked by `pre-bash-check.py`
2. `hooks` — wires hook scripts to Claude Code events (PreToolUse, PostToolUse, Stop, Notification)
