## Context Efficiency

- Maximize output per token of context consumed
- No preamble, trailing summaries, or narration of internal steps
- Parallelize independent tool calls; minimize total tool calls
- Spawn subagents to isolate large tool outputs from the main context
- Prefer targeted grep/find over broad file reads

### Pre-read protocol (mandatory before any file read)

Before reading any file, answer both questions:
1. Does this task, as stated, require knowledge from this file?
2. Has investigation already confirmed this domain is in scope?

If neither is yes, do not read the file.

### Graduated reading order

This order governs investigation-driven reads. A skill's explicit "Always read" Setup items are structural prerequisites — read those first, then follow this order for any additional reads.

1. Read the task description and the user's message (always free)
2. Read `.claude/docs/investigation-tools.md` once per session; use the active tool per category to locate files and symbols
3. Read only the files the tools surfaced
4. Read a domain doc only after step 3 confirms the domain applies

Never read a doc to discover whether it applies — investigate first.

### Session caching

Once a file has been read in a session, never read it again.
