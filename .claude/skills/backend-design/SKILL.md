---
name: backend-design
description: Design and implement backend features. Use this skill when the user wants to build or redesign APIs, services, database models, or backend logic — whether from scratch or modifying existing ones.
---

# Backend Design

## Setup

Always read:
- `.claude/docs/backend.md`
- `.claude/docs/coding.md`
- `.claude/docs/code-style.md`
- `.claude/docs/investigation-tools.md`

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

Understand the existing codebase before touching anything:
- Identify the language, framework, and directory structure using `file_locate` from `.claude/docs/investigation-tools.md`
- Find handlers, services, or models adjacent to the target area using `symbol_search` or `reference_search`
- Note the API conventions, error handling patterns, and validation approach in use

### 2. Design

Decide the structure before writing code:
- API surface: endpoints, methods, request/response shapes, status codes
- Data model: tables/fields/relationships or document structure
- Service boundaries: what this layer is responsible for vs. what it delegates
- Failure modes: what can go wrong and how errors propagate to the caller

State the design in a short summary before implementing.

### 3. Implement

Write the code following the conventions from the rule files. Match the existing codebase style exactly — do not introduce new patterns without reason.

### 4. Verify

- Run existing tests; add an integration or unit test for the changed path if none exist
- Confirm auth, input validation, and error responses are correct
- Check for obvious security issues: injection, missing auth checks, data over-exposure
