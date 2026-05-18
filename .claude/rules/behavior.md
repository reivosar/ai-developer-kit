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
- Worktree creation is Step 0 inside `/coding` — never invoke `/worktree` as a standalone step before `/coding`; all implementation work happens inside the worktree on a `<type>/<desc>` branch; never commit to main
- After committing on a feature branch, immediately invoke `/pull-request` — do not wait for the user to ask
- When `/code-review` returns issues, fix them immediately and re-invoke `/code-review`; repeat until the verdict is Approved — never stop after a "Changes requested" verdict and present it to the user

### Verification

- All completion claims must be backed by observed evidence (test output, command result)
- Do not declare work done until tests pass — inferred success is not success
- Reading a workflow document is not evidence it was followed; follow it, verify it

### Bash commands

- All Bash commands that reference repository paths must use absolute paths derived from `git rev-parse --show-toplevel` or `$REPO_ROOT`; never rely on an implicit working directory. Exception: `find` must be invoked as `find . <pattern>` from the repo root — the allow list only covers this relative-path form; absolute paths are blocked.
- Only issue Bash commands that are listed in `permissions.allow` in `.claude/settings.json`; any command outside that list is rejected by the pre-bash hook and wastes time — check the allow list before running any command
