## Behavior

### File operations

- Never use `rm` — always use `.claude/hooks/trash.sh <file>` to move files to the session trash (`.trash/<timestamp>/`)
- Never stage unstaged files without explicit user request

### Safety

- Ask before any destructive operation — `git reset --hard`, force push
- Never add history-rewriting or destructive git operations (`git rebase*`, `git reset*`, `git push --force*`) to `settings.json` allow list without explicit user approval; do not bundle adjacent permissions not explicitly requested

### Bash commands

- Run every Bash command from the repo root; never rely on a subdirectory working directory. The allow list and the path guards match repo-root-relative paths.
- Use repo-root-relative paths for commands the hooks path-check: `find` must be invoked as `find . <pattern>`, and `python3` / `pytest` script paths must be relative and inside the project — absolute paths and `..` traversal are blocked by `pre-bash.py`.
- Absolute paths are permitted only where the allow list explicitly covers them (e.g. `stat` / `test -f` on `/tmp/ai-developer-kit-update/...` during kit updates).
- Only issue Bash commands that are listed in `permissions.allow` in `.claude/settings.json`; any command outside that list is rejected by the pre-bash hook and wastes time — check the allow list before running any command
