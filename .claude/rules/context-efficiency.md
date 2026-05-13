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

1. Read the task description and the user's message (always free)
2. Run grep/find to locate specific files, symbols, or patterns in scope
3. Read only the files grep/find surfaced
4. Read a doc only after step 2 confirms the domain applies

Never read a doc to discover whether it applies — investigate first.

### Session caching

Once a file has been read in a session, never read it again.
