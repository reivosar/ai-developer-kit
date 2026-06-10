## Behavior

### File operations

- Never use `rm` — always use `.claude/hooks/trash.sh <file>` to move files to the session trash (`.trash/<timestamp>/`)
- Never stage unstaged files without explicit user request

### Safety

- Ask before any destructive operation — `git reset --hard`, force push
- Fix root causes; never suppress errors or skip hooks
- Clarify ambiguous instructions before writing code
- Never add history-rewriting or destructive git operations (`git rebase*`, `git reset*`, `git push --force*`) to `settings.json` allow list without explicit user approval; do not bundle adjacent permissions not explicitly requested

### Language and style

- All project files must be written in English — comments, descriptions, and body text; Japanese is for conversation only; exception: Japanese is permitted in program files where the application requires it (user-facing strings, locale files, UI copy)
- Never use emojis anywhere — not in files, not in responses, not in commit messages; use plain text ("Good:" / "Bad:") instead

### Workflow

- When the next step is unambiguous, invoke the appropriate skill immediately without asking for prior confirmation; reserve pre-action confirmation for destructive or irreversible operations only
- After committing on a feature branch, immediately invoke `/pull-request` — do not wait for the user to ask
- When `/code-review` returns issues, fix them immediately and re-invoke `/code-review`; repeat until the verdict is Approved — never stop after a "Changes requested" verdict and present it to the user

### Verification

- All completion claims must be backed by observed evidence (test output, command result)
- Do not declare work done until tests pass — inferred success is not success
- Reading a workflow document is not evidence it was followed; follow it, verify it

### Memory

Save to memory only when the insight is non-obvious and reusable across future conversations:
- User corrections or confirmed non-default approaches (feedback type)
- Decisions driven by constraints not visible in the code (project type)
- Where to find information in external systems (reference type)

Do NOT save: code patterns derivable from the codebase, task-specific context, anything already in CLAUDE.md, or ephemeral state.

The memory_guard hook enforces the 200-line limit automatically. If MEMORY.md is approaching 180 lines, prune stale or low-value entries before adding new ones.

### Bash commands

- Run every Bash command from the repo root; never rely on a subdirectory working directory. The allow list and the path guards match repo-root-relative paths.
- Use repo-root-relative paths for commands the hooks path-check: `find` must be invoked as `find . <pattern>`, and `python3` / `pytest` script paths must be relative and inside the project — absolute paths and `..` traversal are blocked by `pre-bash.py`.
- Absolute paths are permitted only where the allow list explicitly covers them (e.g. `stat` / `test -f` on `/tmp/ai-developer-kit-update/...` during kit updates).
- Only issue Bash commands that are listed in `permissions.allow` in `.claude/settings.json`; any command outside that list is rejected by the pre-bash hook and wastes time — check the allow list before running any command
