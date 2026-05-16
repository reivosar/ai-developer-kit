---
name: backend-design
description: Design and implement backend features. Use this skill when the user wants to build or redesign APIs, services, database models, or backend logic — whether from scratch or modifying existing ones.
---

# Backend Design

## Setup

Always read:
- `.claude/docs/backend.md`

Read only when the task explicitly involves:
- Task involves implementation with testable logic → `.claude/docs/testing.md`
- Auth, input validation, or external API calls → `.claude/docs/security.md`
- Database tables, schemas, or queries → `.claude/docs/database.md`
- Error handling or failure paths → `.claude/docs/errors.md`
- Log statements → `.claude/docs/logging.md`
- Metrics, health checks, or alerting → `.claude/docs/monitoring.md`

Do not read a conditional file unless the task description or codebase investigation confirms it applies.

## Steps

### 1. Investigate

Invoke /investigate. Note the API conventions, error handling patterns, and validation approach in use.

### 2. Design

Decide the structure before writing code:
- API surface: endpoints, methods, request/response shapes, status codes
- Data model: tables/fields/relationships or document structure
- Service boundaries: what this layer is responsible for vs. what it delegates
- Failure modes: what can go wrong and how errors propagate to the caller

State the design in a short summary before implementing.

### 3. Implement

Invoke /coding with the design from Step 2. /coding handles implementation, review, commit, and PR.
