---
name: documentation
description: Generate or update documentation. Use this skill when the user wants to write or update a README, create an Architecture Decision Record (ADR), generate an OpenAPI spec, or document an API — triggered by phrases like "document this", "write a README", "create an ADR", "generate API docs", "update the docs".
---

# Documentation

## Setup

Read before proceeding:
- `.claude/docs/documentation.md`

## Steps

### 1. Investigate

```bash
find . -name "*.md" -not -path "*/.git/*"
```

If documenting specific code behavior, invoke /investigate to locate the source.

### 2. Write

Invoke /coding with the documentation requirements from Step 1. /coding handles writing, review, commit, and PR.
