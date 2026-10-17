# AI Developer Kit

A Claude Code configuration template for structured, hook-enforced development workflows.

## Overview

This kit provides a complete `.claude/` directory that wires Claude Code into a disciplined development process: tasks are routed to named skills, every file edit is guarded by hooks, commits are blocked if secrets or bad branch names are detected, and all implementation work is isolated in git worktrees. Drop it into any project to get consistent behavior without rebuilding the configuration from scratch.

## Setup

Clone or copy this repository, then symlink or copy the `.claude/` directory into your target project:

```bash
git clone https://github.com/reivosar/ai-developer-kit.git
cp -r ai-developer-kit/.claude /path/to/your-project/.claude
```

Make hooks executable:

```bash
chmod +x .claude/hooks/*.sh .claude/hooks/*.py
```

Open Claude Code in your project directory. The rules, skills, and hooks load automatically.

To have GitHub offer the kit's pull request and issue templates on its pages, copy them into `.github/`. The hooks check pull request and issue bodies against them either way:

```bash
mkdir -p .github
cp -r .claude/templates/github/. .github/
```

The hooks call external tools: flake8, pylint, ruff, yamllint, tsc, Biome, ESLint with eslint-plugin-jsdoc, markdownlint, go, revive, clippy, cargo-llvm-cov, Checkstyle, detekt, pytest, and pytest-cov. Checkstyle and detekt are jars downloaded from their GitHub releases and need a Java runtime, which the kit does not install. When one is missing, `.claude/hooks/install-tool.sh` installs it through Homebrew, apt or yum, pipx, npm, go, or rustup, and installs nothing outside that list. Tools that pipx and go install land in `~/.local/bin`, which the hooks add to PATH themselves. Rust itself is not installed: the Rust tools need rustup to be present. Formatters are not installed: `post-edit.sh` runs prettier, black, gofmt, rubocop, or shfmt only when the project already has it.

## Usage

Invoke skills via slash commands in the Claude Code prompt:

| Command | Purpose |
|---|---|
| `/skill-selector` | Pick the skill for a task when the right one is unclear — optional; invoke a matching skill directly when it is obvious |
| `/worktree` | Create an isolated git worktree before starting any task |
| `/investigate` | Locate the code or files relevant to a task before writing anything |
| `/coding` | Implement a feature or change against a known design |
| `/troubleshooting` | Investigate a bug, error, or failing test |
| `/plan` | Plan a multi-file feature before writing code |
| `/frontend-design` | Design and implement frontend features |
| `/backend-design` | Design and implement backend features |
| `/explain` | Explain a piece of code, function, file, or concept |
| `/explore` | Summarize an unfamiliar codebase or module |
| `/commit` | Create a Conventional Commits-formatted commit |
| `/pull-request` | Open a PR from the current feature branch |
| `/code-review` | Review staged changes or a PR for bugs and quality |
| `/test` | Generate or improve test coverage |
| `/simplify` | Review changed code for quality and refactoring opportunities |
| `/security-review` | Audit pending changes for vulnerabilities |
| `/documentation` | Write or update README, ADR, or OpenAPI docs |
| `/edit-kit` | Modify `settings.json` — permissions, hooks, env vars |
| `/update-kit` | Pull the latest skills and rules from upstream |
| `/feedback` | File a rule or skill gap as a GitHub issue on the kit repository |

Run the hook test suites to verify everything works. The full list is in the Tests section of `CLAUDE.md`; for example:

```bash
pytest .claude/hooks/test_allow_list.py
python3 .claude/hooks/test_hook_lib.py
pytest .claude/hooks/test_docs_sync.py
```

## Architecture

Everything lives under `.claude/`. There is no application code in this repository.

```text
.claude/
  rules/          # Auto-loaded into every conversation
  docs/           # On-demand rule library; skills read only what they need
  skills/         # Slash-command workflows (one directory per skill)
  hooks/          # Python and shell scripts wired to Claude Code hook events
  settings.json   # Permissions allow/deny list and hook wiring
  mcp-allowlist.txt  # MCP tool names that pre-mcp.py lets through
  worktrees/      # Temporary git worktrees created per task (gitignored)
  logs/           # Hook records, one directory per session (gitignored)
  templates/      # Pull request and issue templates the hooks check bodies against
```

### Rules

`.claude/rules/*.md` — loaded automatically into every session, one file per responsibility.

### Rule library

`.claude/docs/*.md` — topic-specific rules (backend, security, testing, git workflow, etc.). Not auto-loaded. Each skill reads only the files it needs.

### Skills

`.claude/skills/<name>/SKILL.md` — step-by-step workflow Claude follows when that skill is invoked. Skills are the primary extension point: add a `SKILL.md` to add a new slash command.

### Hooks

Hook scripts enforce constraints the rules alone cannot:

| Hook | Trigger | Purpose |
|---|---|---|
| `pre-bash.py` | Before every Bash command | Enforces the allow/deny list in `settings.json`; blocks shell syntax that can hide a second command (command substitution, a lone `&`, a second line); blocks merging into `main`, pushing `main`, merging or closing a pull request, git options that force, delete, discard, or overwrite, and `find` actions; runs the `cp`, commit, sensitive-path, and rate-limit guards; blocks `gh pr create` and `gh issue create` when the body does not follow its template; on `git commit`, blocks staged files that fail static analysis and staged Python, Go, Rust, or TypeScript code below 90% coverage |
| `pre-write.py` / `pre-edit.py` | Before file writes/edits | Blocks paths outside the repository or the active worktree, `.env` files, Japanese characters and emoji in content, Markdown documents over 200 lines, names assembled at runtime, tests that break the test rules, public code whose doc comment is missing or does not match its parameters, function bodies longer than 20 lines, and implementation changes without tests; `pre-write.py` also refuses to overwrite an existing file. Without blocking, both return to the agent the references to a changed function and the location of a duplicate function name |
| `pre-mcp.py` | Before every MCP tool call | Checks the tool name against `mcp-allowlist.txt`; applies the rate limit |
| `memory_guard.py` | Before file writes, after file writes/edits | Enforces the 200-line limit on the memory index |
| `post-edit.sh` | After file writes/edits | Runs the installed formatter on the changed file, then the linters on a file inside the project; a finding, such as a code file over 200 lines, is handed back to be fixed at once |
| `post-tool.py` | After Bash commands and file writes/edits | Appends the tool call to the session's audit file |
| `user-prompt-submit.py` | On every user prompt | Prompt injection guard and skill dispatch reminder |
| `block-read.sh` | Before file reads | No-op kept as a wiring point |
| `notify.sh` | On notifications | Sends a desktop notification |
| `on-stop.sh` | When Claude stops | Sends a desktop notification and rings the terminal bell |
| `trash.sh` | On-demand | Moves files to `.trash/<timestamp>/` instead of deleting |

### Records

The hooks write to `.claude/logs/<date>_<session>/`, one directory per session: `audit.jsonl` holds every tool call, and `blocks/<guard>.jsonl` holds one line for each time that check blocked. To see which checks fired in a session and how often:

```bash
wc -l .claude/logs/2026-10-13_5a429071/blocks/*.jsonl
```

### Settings

`settings.json` controls two things:

1. `permissions.allow` / `permissions.deny` — glob patterns checked by `pre-bash.py` before every Bash command. When adding a new allowed command, write a failing test in `test_allow_list.py` first.
2. `hooks` — wires hook scripts to Claude Code events (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Notification`, `Stop`, `SessionStart`).

## Architecture decisions

**Skill dispatch over ad hoc handling** — a task that matches a skill runs through that skill rather than being handled ad hoc; a task that matches none is answered inline. This keeps behavior consistent and auditable; the dispatch table in `.claude/skills/skill-selector/SKILL.md` is the single source of truth.

**Worktree isolation** — all implementation work happens in a git worktree (`.claude/worktrees/<name>/`), never in the main working directory. This prevents accidental commits to `main` and allows parallel workstreams without branch conflicts.

**Hook enforcement over trust** — constraints like the allow/deny list and secret detection are enforced by hooks that run before tool execution, not by prompting Claude to remember rules. The hooks that guard a tool call (`pre-bash.py`, `pre-write.py`, `pre-edit.py`, `pre-mcp.py`, and `memory_guard.py`) fail closed; if one raises, cannot read its input, or cannot be loaded, the action is blocked. `settings.json` starts each of them through `run-hook.py`, which is why a broken guard module, or a syntax error in the hook itself, blocks the action instead of switching the checks off. The prompt hook (`user-prompt-submit.py`) is the exception: blocking every prompt would leave no way to ask for the repair, so a failure there lets the prompt through.

**No destructive operation without the user** — the agent does not merge into `main`, push `main`, merge or close a pull request, force, delete, or discard. The allow list names the safe forms of each command, and `pre-bash.py` checks the options and the shell syntax as well, because a prefix pattern such as `git diff*` alone also matches `git difftool`, and `git status $(gh pr close 1)` would run the command inside it. Commands that run project code (`npm run`, `pytest`) can still do whatever that code does.

**English-only project files** — all rules, skills, docs, hooks, and commit messages are written in English regardless of the user's locale. This keeps the configuration readable by any contributor and avoids encoding issues in shell scripts.
