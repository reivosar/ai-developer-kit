## Behavior

### File operations

- Never use `rm` — always use `.claude/hooks/trash.sh <file>` to move files to the session trash (`.trash/<timestamp>/`)
- Never stage unstaged files without explicit user request

### Safety

- Ask before any destructive operation — `git reset --hard`, force push
- Fix root causes; never suppress errors or skip hooks
- Clarify ambiguous instructions before writing code

### Language and style

- All project files must be written in English — comments, descriptions, and body text; Japanese is for conversation only; exception: Japanese is permitted in program files where the application requires it (user-facing strings, locale files, UI copy)
- Never use emojis anywhere — not in files, not in responses, not in commit messages; use plain text ("Good:" / "Bad:") instead

### Workflow

- When the next step is unambiguous, invoke the appropriate skill immediately without asking for prior confirmation; reserve pre-action confirmation for destructive or irreversible operations only
- Before any task that involves changes: invoke /worktree to create an isolated workspace on a `<type>/<desc>` branch; all implementation work must happen inside the worktree; never commit to main or to an unrelated branch
- Every task must be handled by a skill; never handle any task inline. See `skill-dispatch.md` for the full list. If no skill clearly fits, invoke `/propose`.

### Bash commands

- All Bash commands that reference repository paths must use absolute paths derived from `git rev-parse --show-toplevel` or `$REPO_ROOT`; never rely on an implicit working directory
- Only issue Bash commands that are listed in `permissions.allow` in `.claude/settings.json`; any command outside that list is rejected by the pre-bash hook and wastes time — check the allow list before running any command
