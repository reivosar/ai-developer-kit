## Behavior

- Never use `rm` — always use `.claude/hooks/trash.sh <file>` to move files to the session trash (`.trash/<timestamp>/`)
- Ask before any destructive operation — `git reset --hard`, force push
- Fix root causes; never suppress errors or skip hooks
- Clarify ambiguous instructions before writing code
- All project files must be written in English — comments, descriptions, and body text; Japanese is for conversation only; exception: Japanese is permitted in program files where the application requires it (user-facing strings, locale files, UI copy)
- Never use emojis anywhere — not in files, not in responses, not in commit messages; use plain text ("Good:" / "Bad:") instead
- When the next step is unambiguous, commit without asking for confirmation; reserve confirmation for destructive or irreversible actions only
- Never stage unstaged files without explicit user request
- Before any task that involves changes: invoke /worktree to create an isolated workspace on a `<type>/<desc>` branch; all implementation work must happen inside the worktree; never commit to main or to an unrelated branch
- All Bash commands that reference repository paths must use absolute paths derived from `git rev-parse --show-toplevel` or `$REPO_ROOT`; never rely on an implicit working directory
- Only issue Bash commands that are listed in `permissions.allow` in `.claude/settings.json`; any command outside that list is rejected by the pre-bash hook and wastes time — check the allow list before running any command
- Every task must be handled through a skill listed in `skill-dispatch.md`; never handle any task inline — if no skill clearly fits, invoke `/feedback` to file a skill-gap issue
