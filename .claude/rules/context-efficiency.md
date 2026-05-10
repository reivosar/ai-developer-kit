## Context Efficiency

- Maximize output per token of context consumed
- No preamble, trailing summaries, or narration of internal steps
- Parallelize independent tool calls; minimize total tool calls
- Read only files directly relevant to the task; never read speculatively
- Spawn subagents to isolate large tool outputs from the main context
- Prefer targeted grep/find over broad file reads
