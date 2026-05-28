---
name: documentation
description: Generate or update documentation. Use this skill when the user wants to write or update a README, create an Architecture Decision Record (ADR), generate an OpenAPI spec, or document an API — triggered by phrases like "document this", "write a README", "create an ADR", "generate API docs", "update the docs".
---

# Documentation

## Setup

Always read:
- `.claude/docs/documentation.md`

## Steps

### 1. Investigate

Use the **find-docs** command from `commands.md`.

If documenting specific code behavior, invoke /investigate to locate the source.

### 2. Write

Invoke /coding with the documentation requirements from Step 1. Ask /coding to stop before committing — writing and review only.

### 3. Humanize

Invoke /humanize-ai-doc on the generated documentation files to remove AI writing patterns and improve readability.

### 4. Commit and PR

Invoke /commit, then /pull-request.
