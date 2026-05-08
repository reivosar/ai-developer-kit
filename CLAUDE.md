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

- Frontend tasks (HTML/CSS/JS/TS/React/Vue/etc.) → `/frontend`
- Backend tasks (APIs/services/DB/server-side) → `/backend`
- General/ambiguous coding, scripts, CLI, full-stack → `/coding`
- Planning a feature → `/plan`
- Reviewing changes → `/code-review`
- Committing → `/commit`
- Worktree operations → `/worktree`

Once a rule file from `.claude/rule-library/` has been read in a session, never read it again — treat it as cached.
