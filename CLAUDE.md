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
python3 .claude/hooks/test_post_edit.py
python3 .claude/hooks/test_block_read.py
python3 .claude/hooks/test_hook_lib.py
python3 .claude/hooks/test_content_guard.py
python3 .claude/hooks/test_trash_sh.py
python3 .claude/hooks/test_notify.py
pytest .claude/hooks/test_prompt_injection_guard.py
pytest .claude/hooks/test_mcp_guard.py
pytest .claude/hooks/test_audit_log.py
pytest .claude/hooks/test_rate_limiter.py
pytest .claude/hooks/test_anomaly_guard.py
pytest .claude/hooks/test_memory_guard.py
pytest .claude/hooks/test_worktree_guard.py
```

`test_coverage.py` additionally requires `pip install coverage`.

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
- `pre-bash.py` — PreToolUse[Bash]: allow/deny list + git/cp guards + commit checks + anomaly guard
- `pre-write.py` — PreToolUse[Write]: env file guard + file-exists guard + content guard + TDD guard + worktree guard
- `pre-edit.py` — PreToolUse[Edit]: env file guard + content guard + TDD guard + worktree guard
- `pre-mcp.py` — PreToolUse[mcp__.*]: MCP tool allowlist + rate limiting + audit log
- `post-edit.sh` — PostToolUse[Write|Edit]: auto-format; prints WARNING on formatter failure
- `post-tool.py` — PostToolUse[Bash|Write|Edit]: audit logging
- `user-prompt-submit.py` — UserPromptSubmit: prompt injection guard + skill dispatch reminder
- `memory_guard.py` — PreToolUse[Write] + PostToolUse[Write|Edit]: enforces MEMORY.md 200-line limit
- `block-read.sh` — PreToolUse[Read]: currently a no-op (`exit 0`); kept as a wiring point
- `notify.sh` — Notification: desktop notification per notification_type
- `on-stop.sh` — Stop: desktop notification + terminal bell
- SessionStart runs an inline `chmod +x` over hook scripts (no script file)

Guard modules (imported by entry points):
- `bash_guard.py`, `git_guard.py`, `cp_guard.py` — Bash safety checks
- `commit_guard.py` — secret detection, branch name, whitespace, .env, emoji in staged diff
- `env_file_guard.py` — blocks writes to .env files
- `content_guard.py` — blocks Japanese characters and emoji in file content
- `tdd_guard.py` — blocks impl edits without staged tests covering modified functions
- `worktree_guard.py` — when running inside `.claude/worktrees/<name>`, blocks writes outside that worktree
- `anomaly_guard.py` — blocks sensitive system paths (`~/.ssh`, `/etc/passwd`, ...) and paths escaping the repo root
- `prompt_injection_guard.py` — blocks prompt injection patterns in user prompts
- `mcp_guard.py` — checks MCP tool names against `.claude/mcp-allowlist.txt`
- `audit_log.py` — appends tool invocations to `.claude/audit.log`
- `rate_limiter.py` — per-session rate limiting backed by `.claude/rate-state.json`
- `hook_lib.py` — shared utilities (REPO_ROOT, block(), read_stdin_json())
- `trash.sh` — moves files to `.trash/<timestamp>/`; always use this instead of `rm`
- `static-analysis.sh` — standalone lint runner invoked as an allowed Bash command

### Settings

`.claude/settings.json` — two concerns:

1. `permissions.allow` / `permissions.deny` — Bash command patterns checked by `pre-bash.py`
2. `hooks` — wires hook scripts to Claude Code events (PreToolUse, PostToolUse, UserPromptSubmit, Notification, Stop, SessionStart)

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
