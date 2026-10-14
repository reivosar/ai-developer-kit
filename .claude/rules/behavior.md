## Behavior

### File operations

- Never use `rm` — always use `.claude/hooks/trash.sh <file>` to move files to the session trash (`.trash/<timestamp>/`)
- Never stage unstaged files without explicit user request

### Safety

- Ask before any destructive operation — `git reset --hard`, force push
- Never add history-rewriting or destructive git operations (`git rebase*`, `git reset*`, `git push --force*`) to `settings.json` allow list without explicit user approval; do not bundle adjacent permissions not explicitly requested
- Never merge into `main`, push `main`, or merge or close a pull request — the user does these. `pre-bash.py` blocks them, and blocks git options that force, delete, discard, or overwrite (`--force`, `-f`, `--discard-changes`, `--delete`, `--output`, and more per subcommand); ask the user to run such a command instead of looking for another form of it

### Bash commands

- Run every Bash command from the repo root; never rely on a subdirectory working directory. The allow list and the path guards match repo-root-relative paths.
- Use repo-root-relative paths for commands the hooks path-check: `find` must be invoked as `find . <pattern>`, and `python3` / `pytest` script paths must be relative and inside the project — absolute paths and `..` traversal are blocked by `pre-bash.py`.
- Write one command per line. `pre-bash.py` blocks shell syntax that can hide a second command: command substitution (`$(...)` and backticks, also inside double quotes), process substitution, a lone `&`, a second line (so a here-document too), and `$'...'` quoting. Pass multi-line text through a file: `git commit -F <file>`, `gh pr create --body-file <file>`.
- `find` may only list files; `-delete`, `-exec`, `-execdir`, `-ok`, and the `-fprint` actions are blocked.
- Absolute paths are permitted only where the allow list explicitly covers them (e.g. `stat` / `test -f` on `/tmp/ai-developer-kit-update/...` during kit updates).
- When a step fails because a tool is missing, install the tool with `.claude/hooks/install-tool.sh <tool>` and run the step again; never skip the step. `.claude/hooks/install-tool.sh --list` prints the tools it installs. When the tool is not on that list, report the missing tool instead of working around it.
- Only issue Bash commands that are listed in `permissions.allow` in `.claude/settings.json`; any command outside that list is rejected by the pre-bash hook and wastes time — check the allow list before running any command
