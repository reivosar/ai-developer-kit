## Memory

Save to memory only when the insight is non-obvious and reusable across future conversations:
- User corrections or confirmed non-default approaches (feedback type)
- Decisions driven by constraints not visible in the code (project type)
- Where to find information in external systems (reference type)

Do NOT save: code patterns derivable from the codebase, task-specific context, anything already in CLAUDE.md, or ephemeral state.

The memory_guard hook enforces the 200-line limit automatically. If MEMORY.md is approaching 180 lines, prune stale or low-value entries before adding new ones.
