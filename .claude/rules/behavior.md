## Behavior

- Never use `rm` — always use `.claude/hooks/trash.sh <file>` to move files to the session trash (`.trash/<timestamp>/`)
- Ask before any destructive operation — `git reset --hard`, force push
- Fix root causes; never suppress errors or skip hooks
- Clarify ambiguous instructions before writing code
- All project files must be written in English — comments, descriptions, and body text; Japanese is for conversation only; exception: Japanese is permitted in program files where the application requires it (user-facing strings, locale files, UI copy)
- Never use emojis anywhere — not in files, not in responses, not in commit messages; use plain text ("Good:" / "Bad:") instead
- When the next step is unambiguous, commit without asking for confirmation; reserve confirmation for destructive or irreversible actions only
- Before any task that involves changes: `git checkout main` → `git pull` → `git checkout -b <type>/<desc>`; never commit to main or to an unrelated branch
