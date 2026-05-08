# AI Developer Kit

Template kit for Claude Code-powered development workflows.
Rules are in `.claude/rules/`.

## Behavior

- Ask before any destructive operation — `rm`, `git reset --hard`, force push
- Fix root causes; never suppress errors or skip hooks
- Clarify ambiguous instructions before writing code
