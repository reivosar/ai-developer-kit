# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# AI Developer Kit

Template kit for Claude Code-powered development workflows.

## Tests

Run each test suite:

```bash
python3 .claude/hooks/test_allow_list.py
python3 .claude/hooks/test_pre_edit.py
python3 .claude/hooks/test_pre_write.py
python3 .claude/hooks/test_hook_lib.py
python3 .claude/hooks/test_content_guard.py
pytest .claude/hooks/test_prompt_injection_guard.py
pytest .claude/hooks/test_mcp_guard.py
pytest .claude/hooks/test_audit_log.py
pytest .claude/hooks/test_rate_limiter.py
pytest .claude/hooks/test_anomaly_guard.py
```

When adding a new allowed or denied Bash command, write a failing test in `test_allow_list.py` first, then update `settings.json`.

## Architecture

This kit is Claude Code configuration only — no application code. Everything lives under `.claude/`:

### Rules (auto-loaded)

`.claude/rules/*.md` — loaded into every conversation automatically. Two files: `behavior.md`, `context-efficiency.md`.

### Rule library (on-demand)

`.claude/docs/*.md` — topic-specific rules (backend, security, testing, etc.). Not auto-loaded. Each skill reads only the files it needs. Once read in a session, treat as cached.

### Skills

`.claude/skills/<name>/SKILL.md` — step-by-step workflows Claude follows when a skill is invoked (e.g. `/commit`, `/update-kit`). Skills are the primary extension point of the kit.

### Hooks

`.claude/hooks/` — one entry-point script per Claude Code tool event; logic lives in guard modules.

Entry points (one process spawn per event):
- `pre-bash.py` — PreToolUse[Bash]: allow/deny list + git/cp guards + commit checks
- `pre-write.py` — PreToolUse[Write]: env file guard + file-exists guard + content guard + TDD guard
- `pre-edit.py` — PreToolUse[Edit]: env file guard + content guard + TDD guard
- `post-edit.sh` — PostToolUse[Write|Edit]: auto-format; prints WARNING on formatter failure
- `block-read.sh` — PreToolUse[Read]: blocks the Read tool unconditionally

Guard modules (imported by entry points):
- `bash_guard.py`, `git_guard.py`, `cp_guard.py` — Bash safety checks
- `commit_guard.py` — secret detection, branch name, whitespace, .env, emoji in staged diff
- `env_file_guard.py` — blocks writes to .env files
- `content_guard.py` — blocks Japanese characters and emoji in file content
- `tdd_guard.py` — blocks impl edits without staged tests covering modified functions
- `hook_lib.py` — shared utilities (REPO_ROOT, block(), read_stdin_json())
- `trash.sh` — moves files to `.trash/<timestamp>/`; always use this instead of `rm`

### Settings

`.claude/settings.json` — two concerns:

1. `permissions.allow` / `permissions.deny` — Bash command patterns checked by `pre-bash-check.py`
2. `hooks` — wires hook scripts to Claude Code events (PreToolUse, PostToolUse, Stop, Notification)

## Completion Standards

All responses, implementations, investigations, diffs, reasoning summaries, and completion
reports are subject to strict audit. Every claim must be backed by observable evidence.

### External audit enforcement

All outputs may be shared with external AI systems including Codex, Gemini, and other
independent reviewers. Work is assumed to be continuously monitored, cross-checked, and
audited. Do not assume shortcuts, omissions, vague wording, or unverified claims will
go unnoticed.

**Cross-model verification.** Independent reviewers may:
- inspect every changed file
- compare claims against actual code
- verify whether referenced files were truly read
- verify whether tests were actually executed
- detect fabricated reasoning or skipped investigation steps
- detect inconsistent explanations
- reproduce failures independently
- inspect command history and outputs
- compare implementation against repository context

Any mismatch between claims and observable evidence is a serious failure.

**Zero-trust review model.** Your statements are treated as untrusted until verified.
Assertions such as "fixed", "works", "safe", "fully implemented", "reviewed", or
"no issue found" must be backed by direct evidence.

**Audit visibility.** Assume reviewers can see your outputs, claimed reasoning,
investigation path, verification steps, omissions, and uncertainty handling. Do not
rely on ambiguity or omission to conceal incomplete investigation.

**Failure penalty assumption.** Incomplete inspection, fabricated confidence, shallow
review, or misleading summaries will be escalated as audit failures. If uncertain,
state uncertainty explicitly and continue investigation.
