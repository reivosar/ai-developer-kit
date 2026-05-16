# AI Developer Kit

A Claude Code configuration template for structured, hook-enforced development workflows.

## Overview

This kit provides a complete `.claude/` directory that wires Claude Code into a disciplined development process: every task goes through a named skill, every file edit is guarded by hooks, commits are blocked if secrets or bad branch names are detected, and all implementation work is isolated in git worktrees. Drop it into any project to get consistent behavior without rebuilding the configuration from scratch.

## Setup

Clone or copy this repository, then symlink or copy the `.claude/` directory into your target project:

```bash
git clone https://github.com/reivosar/ai-developer-kit.git
cp -r ai-developer-kit/.claude /path/to/your-project/.claude
```

Make hooks executable:

```bash
chmod +x .claude/hooks/*.sh
```

Open Claude Code in your project directory. The rules, skills, and hooks load automatically.

## Usage

Invoke skills via slash commands in the Claude Code prompt:

| Command | Purpose |
|---|---|
| `/worktree` | Create an isolated git worktree before starting any task |
| `/coding` | Implement a feature or change against a known design |
| `/troubleshooting` | Investigate a bug, error, or failing test |
| `/plan` | Plan a multi-file feature before writing code |
| `/commit` | Create a Conventional Commits-formatted commit |
| `/pull-request` | Open a PR from the current feature branch |
| `/code-review` | Review staged changes or a PR for bugs and quality |
| `/test` | Generate or improve test coverage |
| `/simplify` | Review changed code for quality and refactoring opportunities |
| `/security-review` | Audit pending changes for vulnerabilities |
| `/documentation` | Write or update README, ADR, or OpenAPI docs |
| `/edit-kit` | Modify `settings.json` — permissions, hooks, env vars |
| `/update-kit` | Pull the latest skills and rules from upstream |

Run the hook test suite to verify everything works:

```bash
.claude/hooks/test_hooks.sh
```

Run individual suites:

```bash
python3 .claude/hooks/test_allow_list.py
python3 .claude/hooks/test_pre_edit_check.py
```

## Architecture

Everything lives under `.claude/`. There is no application code in this repository.

```
.claude/
  rules/          # Auto-loaded into every conversation
  docs/           # On-demand rule library; skills read only what they need
  skills/         # Slash-command workflows (one directory per skill)
  hooks/          # Python and shell scripts wired to Claude Code hook events
  settings.json   # Permissions allow/deny list and hook wiring
  worktrees/      # Temporary git worktrees created per task (gitignored)
```

### Rules

`.claude/rules/*.md` — three files loaded automatically into every session:

- `behavior.md` — hard rules: no `rm`, English-only files, no emojis, worktree-first
- `context-efficiency.md` — token discipline: parallel tools, targeted reads, no preamble
- `skill-dispatch.md` — routing table mapping every task type to a skill

### Rule library

`.claude/docs/*.md` — topic-specific rules (backend, security, testing, git workflow, etc.). Not auto-loaded. Each skill reads only the files it needs.

### Skills

`.claude/skills/<name>/SKILL.md` — step-by-step workflow Claude follows when that skill is invoked. Skills are the primary extension point: add a `SKILL.md` to add a new slash command.

### Hooks

Hook scripts enforce constraints the rules alone cannot:

| Hook | Trigger | Purpose |
|---|---|---|
| `pre-bash.sh` | Before every Bash command | Enforces the allow/deny list in `settings.json` |
| `pre-commit.sh` | Before `git commit` | Blocks secrets, bad branch names, trailing whitespace |
| `pre-edit.sh` / `pre-write.sh` | Before file edits/writes | Guards file mutations |
| `pre-edit-check.py` / `pre-write-check.py` | Before file edits/writes | Additional edit guards |
| `pre-worktree-check.py` | Before file edits/writes | Blocks edits outside a worktree |
| `post-edit.sh` | After file edits/writes | Post-mutation side effects |
| `notify.sh` | On notifications | Surfaces Claude Code notifications |
| `on-stop.sh` | When Claude stops | Cleanup and summary on session end |
| `trash.sh` | On-demand | Moves files to `.trash/<timestamp>/` instead of deleting |

### Settings

`settings.json` controls two things:

1. `permissions.allow` / `permissions.deny` — glob patterns checked by `pre-bash.sh` before every Bash command. When adding a new allowed command, write a failing test in `test_allow_list.py` first.
2. `hooks` — wires hook scripts to Claude Code events (`PreToolUse`, `PostToolUse`, `Stop`, `Notification`).

## Architecture decisions

**Skill-dispatch over inline responses** — every task routes through a named skill rather than being handled ad hoc. This keeps behavior consistent and auditable; the routing table in `skill-dispatch.md` is the single source of truth.

**Worktree isolation** — all implementation work happens in a git worktree (`.claude/worktrees/<name>/`), never in the main working directory. This prevents accidental commits to `main` and allows parallel workstreams without branch conflicts.

**Hook enforcement over trust** — constraints like the allow/deny list and secret detection are enforced by hooks that run before tool execution, not by prompting Claude to remember rules. Hooks fail closed; if a hook errors, the action is blocked.

**English-only project files** — all rules, skills, docs, hooks, and commit messages are written in English regardless of the user's locale. This keeps the configuration readable by any contributor and avoids encoding issues in shell scripts.
