# AI Developer Kit

Template kit for Claude Code-powered development workflows.
Rules are in `.claude/rules/`.

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
