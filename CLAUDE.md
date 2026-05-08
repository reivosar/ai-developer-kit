# AI Developer Kit

Template kit for Claude Code-powered development workflows.

## Behavior

- Never use `rm` — always use `.claude/hooks/trash.sh <file>` to move files to the session trash (`.trash/<timestamp>/`)
- Ask before any destructive operation — `git reset --hard`, force push
- Fix root causes; never suppress errors or skip hooks
- Clarify ambiguous instructions before writing code

## Context Efficiency

- Maximize output per token of context consumed
- No preamble, trailing summaries, or narration of internal steps
- Parallelize independent tool calls; minimize total tool calls
- Read only files directly relevant to the task; never read speculatively
- Spawn subagents to isolate large tool outputs from the main context
- Prefer targeted grep/find over broad file reads

## Skill Dispatch

Always invoke the corresponding skill — never handle these tasks inline:

- All coding (implementation against a known design) → `/coding`
- Bug / error / test failure investigation → `/troubleshooting`
- Creating a pull request → `/pull-request`
- Reviewing a PR or branch → `/code-review`
- Frontend architecture/design (component design, state management, routing design) → `/frontend-design`
- Backend architecture/design (API design, DB model, service boundaries) → `/backend-design`
- Planning a multi-file feature → `/plan`
- Reviewing changes → `/code-review`
- Committing → `/commit`
- Worktree operations → `/worktree`
- Documentation (README, ADR, OpenAPI spec) → `/documentation`

When to use `/coding` vs. a design skill: use a design skill when the structure or boundaries are undecided; use `/coding` once the design is settled and the task is implementation.

Once a rule file from `.claude/rule-library/` has been read in a session, never read it again — treat it as cached.
