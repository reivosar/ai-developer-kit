# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# AI Developer Kit

Template kit for Claude Code-powered development workflows.

## Tests

Run each test suite (one line per module under test):

```bash
python3 .claude/hooks/test_pre_edit.py
python3 .claude/hooks/test_pre_write.py
python3 .claude/hooks/test_post_edit.py
python3 .claude/hooks/test_block_read.py
python3 .claude/hooks/test_hook_lib.py
python3 .claude/hooks/test_content_guard.py
python3 .claude/hooks/test_trash_sh.py
python3 .claude/hooks/test_notify.py
pytest .claude/hooks/test_allow_list.py .claude/hooks/test_allow_list_git.py .claude/hooks/test_allow_list_git_options.py .claude/hooks/test_allow_list_commands.py
pytest .claude/hooks/test_bash_guard.py .claude/hooks/test_find_guard.py
pytest .claude/hooks/test_git_guard.py .claude/hooks/test_git_guard_options.py
pytest .claude/hooks/test_cp_guard.py
pytest .claude/hooks/test_prompt_injection_guard.py
pytest .claude/hooks/test_mcp_guard.py
pytest .claude/hooks/test_audit_log.py .claude/hooks/test_hook_records.py
pytest .claude/hooks/test_rate_limiter.py
pytest .claude/hooks/test_anomaly_guard.py
pytest .claude/hooks/test_memory_guard.py
pytest .claude/hooks/test_worktree_guard.py
pytest .claude/hooks/test_pre_bash_audit_rate.py .claude/hooks/test_pre_edit_path_escape.py .claude/hooks/test_pre_write_audit.py
pytest .claude/hooks/test_docs_sync.py .claude/hooks/test_hook_modules_documented.py
pytest .claude/hooks/test_doc_length_guard.py
pytest .claude/hooks/test_static_analysis.py .claude/hooks/test_static_analysis_file_length.py .claude/hooks/test_static_analysis_guard.py .claude/hooks/test_static_analysis_projects.py
pytest .claude/hooks/test_install_tool.py .claude/hooks/test_install_tool_rust_and_go.py .claude/hooks/test_install_tool_failures.py .claude/hooks/test_setup.py
pytest .claude/hooks/test_function_definitions.py
pytest .claude/hooks/test_dynamic_name_guard.py
pytest .claude/hooks/test_reference_notice.py .claude/hooks/test_reference_notice_hooks.py
pytest .claude/hooks/test_tdd_guard.py .claude/hooks/test_tdd_guard_upstream.py
pytest .claude/hooks/test_testing_guard.py .claude/hooks/test_testing_guard_checks.py
pytest .claude/hooks/test_doc_comments.py .claude/hooks/test_python_doc_comments.py .claude/hooks/test_doc_comments_go_rust.py .claude/hooks/test_doc_comment_shapes.py
pytest .claude/hooks/test_doc_comment_guard.py .claude/hooks/test_doc_comment_guard_checks.py
pytest .claude/hooks/test_function_length_guard.py .claude/hooks/test_function_lengths.py
pytest .claude/hooks/test_template_guard.py .claude/hooks/test_template_guard_templates.py
pytest .claude/hooks/test_hook_lib_helpers.py
pytest .claude/hooks/test_fail_closed.py .claude/hooks/test_fail_closed_handlers.py
pytest .claude/hooks/test_commit_guard.py
pytest .claude/hooks/test_coverage_guard.py .claude/hooks/test_coverage_guard_kit.py .claude/hooks/test_coverage_guard_languages.py .claude/hooks/test_python_coverage.py
pytest .claude/hooks/test_coverage_runners.py .claude/hooks/test_coverage_runners_typescript.py
pytest .claude/hooks/test_entry_points.py
pytest .claude/hooks/test_env_file_guard.py
pytest .claude/hooks/test_post_edit_lint.py
```

`pytest .claude/hooks/test_coverage.py` runs the pytest-style suites under coverage and fails when a hook module falls below 90% branch or line coverage. It needs `pytest-cov`. Every hook module is measured, with no exemption list: a test that starts a hook as its own process runs it with `sys.executable`, and coverage follows that process. A commit that stages a Python file under `.claude/hooks/` runs this test and is blocked when it fails.

When adding a new allowed or denied Bash command, write a failing test in `test_allow_list.py` first, then update `settings.json`.

## Architecture

This kit is Claude Code configuration only — no application code. Everything lives under `.claude/`:

### Rules (auto-loaded)

`.claude/rules/*.md` — loaded into every conversation automatically, one file per responsibility.

### Rule library (on-demand)

`.claude/docs/*.md` — topic-specific rules (backend, security, testing, etc.). Not auto-loaded. Each skill reads only the files it needs. Once read in a session, treat as cached.

### Skills

`.claude/skills/<name>/SKILL.md` — step-by-step workflows Claude follows when a skill is invoked (e.g. `/commit`, `/update-kit`). Skills are the primary extension point of the kit.

### Hooks

`.claude/hooks/` — one entry-point script per Claude Code tool event; logic lives in guard modules.

Entry points (one process spawn per event):
- `pre-bash.py` — PreToolUse[Bash]: shell syntax guard + allow/deny list + git/cp/find guards + template guard + commit checks + static analysis guard + coverage guard + anomaly guard
- `pre-write.py` — PreToolUse[Write]: env file guard + file-exists guard + content guard + document length guard + dynamic name guard + testing guard + doc comment guard + function length guard + TDD guard + worktree guard + reference notice
- `pre-edit.py` — PreToolUse[Edit]: env file guard + content guard + document length guard + dynamic name guard + testing guard + doc comment guard + function length guard + TDD guard + worktree guard + reference notice
- `pre-mcp.py` — PreToolUse[mcp__.*]: MCP tool allowlist + rate limiting + audit log
- `post-edit.sh` — PostToolUse[Write|Edit]: auto-format, then run `static-analysis.sh` on the changed file when it is inside the project and exit 2 with its findings, so the agent fixes them at once
- `post-tool.py` — PostToolUse[Bash|Write|Edit]: audit logging
- `user-prompt-submit.py` — UserPromptSubmit: prompt injection guard + skill dispatch reminder
- `memory_guard.py` — PreToolUse[Write] + PostToolUse[Write|Edit]: enforces MEMORY.md 200-line limit
- `block-read.sh` — PreToolUse[Read]: currently a no-op (`exit 0`); kept as a wiring point
- `notify.sh` — Notification: desktop notification per notification_type
- `on-stop.sh` — Stop: desktop notification + terminal bell
- SessionStart runs an inline `chmod +x` over hook scripts (no script file)

Guard modules (imported by entry points):
- `bash_guard.py` — splits a command into segments (quotes and backslash escapes read as the shell reads them) and checks it against the allow and deny lists; blocks shell syntax that can hide a second command (`$(...)`, backticks, `<(...)`, a lone `&`, a second line, `$'...'`, redirects, pipes), `find` actions, and script paths outside the project
- `git_guard.py` — blocks `git stash drop`/`clear`, `git checkout --`, `git branch -D`, a commit or push on `main`, options that force, delete, discard, or overwrite (listed per subcommand), `git fetch` into a local branch, `git add` of every file, and a git subcommand the allow list does not name (`git difftool` matched `git diff*`)
- `cp_guard.py` — blocks `cp` from outside the project and its forcing options; moves an existing destination to the trash first
- `commit_guard.py` — secret detection, branch name, whitespace, .env, emoji in staged diff
- `coverage_guard.py` — on `git commit`, runs the tests under coverage and blocks when a staged Python, Go, Rust, or TypeScript file outside `.claude/` is below 90%; Python is measured here with pytest-cov, which is installed with pytest when either is missing. A staged Python file under `.claude/hooks/` runs `test_coverage.py` instead, so a kit change below 90% is blocked too
- `coverage_runners.py` — measures Go (`go test -coverprofile`), Rust (`cargo llvm-cov`), and TypeScript (vitest or jest) for `coverage_guard.py` and returns a percent per file
- `env_file_guard.py` — blocks writes to .env files
- `content_guard.py` — blocks Japanese characters and emoji in file content
- `doc_length_guard.py` — blocks a Write or Edit that takes a Markdown document past 200 lines
- `dynamic_name_guard.py` — blocks a Write or Edit that adds a name assembled from strings at runtime
- `reference_notice.py` — does not block; returns to the agent the references to a changed function and the location of a function name that is already defined elsewhere
- `function_definitions.py` — finds function definitions by file extension; shared by `tdd_guard.py` and `reference_notice.py`
- `testing_guard.py` — blocks a Write or Edit that adds a test with no assertion, an always-true assertion, sleep, a snapshot, or a name outside the convention
- `doc_comment_guard.py` — blocks a Write or Edit that adds a public function, method, or type with no doc comment, or with one whose parameter list does not match the signature
- `doc_comments.py` — finds public definitions with their doc comment and parameters (Python, Go, JavaScript, TypeScript, Rust, Java, Kotlin); used by `doc_comment_guard.py`
- `function_length_guard.py` — blocks a Write or Edit that adds a function body longer than 20 lines, or lengthens one that is already longer (Python, Go, JavaScript, TypeScript, Rust, Java, Kotlin)
- `static_analysis_guard.py` — on `git commit`, runs `static-analysis.sh` on the staged files and blocks when it reports a problem
- `template_guard.py` — blocks `gh pr create`, `gh pr edit`, `gh issue create`, and `gh issue edit` when the body lacks a required section of its template or leaves a section empty; the templates are the project's own under `.github/`, or the kit's under `.claude/templates/github/`
- `tdd_guard.py` — blocks impl edits without staged tests covering modified functions
- `worktree_guard.py` — when running inside `.claude/worktrees/<name>`, blocks writes outside that worktree
- `anomaly_guard.py` — blocks sensitive system paths (`~/.ssh`, `/etc/passwd`, ...) and paths escaping the repo root
- `prompt_injection_guard.py` — blocks prompt injection patterns in user prompts
- `mcp_guard.py` — checks MCP tool names against `.claude/mcp-allowlist.txt`
- `audit_log.py` — appends each tool call to `audit.jsonl` in the session's record directory
- `rate_limiter.py` — per-session rate limiting backed by `.claude/rate-state.json`, or by the file `RATE_STATE_FILE` names
- `fail_closed.py` — standard library only; turns an uncaught error into a block (exit 2)
- `run-hook.py` — the launcher `settings.json` uses for `pre-bash.py`, `pre-write.py`, `pre-edit.py`, `pre-mcp.py`, and `memory_guard.py`; it installs `fail_closed` first, so an error while a hook loads, or a syntax error in the hook, blocks the tool call
- `hook_lib.py` — shared utilities (REPO_ROOT, block(), run_fail_closed(), read_hook_input(), emit_additional_context(), read_stdin_json(), read_text(), apply_edit(), tail_lines()); `block()` records each block before it exits
- `hook_records.py` — where records go (records_dir(), remember_session(), session_records_dir(), append_record(), utc_now()); used by `hook_lib.py` and `audit_log.py`
- `find_guard.py` — blocks `find` actions (`-delete`, `-exec`, ...); used by `pre-bash.py`
- `python_coverage.py` — measures Python with pytest-cov for `coverage_guard.py`, installing pytest and pytest-cov first when either is missing
- `doc_comment_shapes.py`, `python_doc_comments.py` — the per-language definition patterns, and the Python reader, behind `doc_comments.py`
- `function_lengths.py` — measures function bodies per language for `function_length_guard.py`
- `hook-lib.sh` — shared utilities for shell hooks (HOOKS_DIR, REPO_ROOT); sourced by `trash.sh`
- `trash.sh` — moves files to `.trash/<timestamp>/`; always use this instead of `rm`
- `static-analysis.sh` — lint runner, called by `post-edit.sh`, by the commit check, and as an allowed Bash command; installs a missing linter before running it; adds the 200-line file limit from `lint-config/` (pylint, Biome or ESLint, revive)
- `project-checks.sh` — sourced by `static-analysis.sh`; runs `go vet`, `tsc`, and `cargo clippy` once in each project a file belongs to (nearest `go.mod`, `tsconfig.json`, `Cargo.toml`), not in the current directory
- `install-tool.sh` — installs a missing tool the hooks call (pipx, npm, go, flake8, yamllint, pytest, pytest-cov, tsc, markdownlint, biome, cargo-clippy, cargo-llvm-cov, pylint, revive) and accepts no other name; an allowed Bash command, also called by `static-analysis.sh`, `coverage_guard.py`, and `setup.sh`
- `conftest.py` — pytest fixtures: hook records in a temporary directory for every test, `tool_stubs` (a PATH of stand-in commands for tests that run the shell scripts), and `pre_bash_blocks` (runs `pre-bash.py` on a command for the allow-list suites)

### Templates

`.claude/templates/github/` — the pull request template and the issue templates (bug report, feature request, kit feedback). `.github/` holds identical copies so GitHub offers them on its pages; `test_template_guard.py` fails when a copy differs. Change a template in `.claude/templates/github/` and copy it to `.github/`. The source of each section is listed in `.claude/docs/git-workflow.md`.

### Records

`.claude/logs/<date>_<session>/` — one directory per session, named by the UTC date of the session's first record and the first eight characters of its session id (`2026-10-13_5a429071`). Git ignores `.claude/logs/`.

- `audit.jsonl` — every tool call, written by `audit_log.py`
- `blocks/<guard>.jsonl` — one line per block, in the file of the guard that blocked it; `wc -l .claude/logs/<date>_<session>/blocks/*.jsonl` counts a session's blocks per check

A hook failure is recorded under `hook_lib`. A failure while a hook loads (`fail_closed.py`) is not recorded. Tests write to a temporary directory: `conftest.py` and the script-style suites set `HOOK_RECORDS_DIR` and `RATE_STATE_FILE`.

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
