---
name: backend-design
description: Backend design skill for planning and designing API structure, service architecture, database schema, and system interactions. Use this skill when the task involves designing how a backend feature should be structured — endpoints, data models, service boundaries, error handling strategy — before or instead of writing code. Trigger for backend architecture decisions, schema design, or "how should we build this API/service?" questions.
---

# Backend Design

Design the structure, architecture, and approach for backend work before implementation begins.

## Setup

Read the following rule files before proceeding:
- `.claude/rule-library/code-style.md`

## Arguments

The design goal or question is passed as `$ARGUMENTS`. If existing code is relevant, read it first.

## Process

### 1. Understand the requirement

Before proposing anything:

- Clarify what the user is trying to build and why
- Identify constraints: existing framework, database, auth system, performance requirements
- Check what already exists in the codebase that's relevant

### 2. Design

Produce a concrete design covering:

- **API surface**: endpoints, methods, request/response shapes, status codes
- **Data model**: tables/collections, fields, relationships, indexes
- **Service boundaries**: what each service/module is responsible for
- **Error handling**: what can fail, how errors propagate, what the caller receives
- **Security**: auth requirements, input validation points, data exposure risks
- **Tradeoffs**: alternatives considered and why this approach was chosen

### 3. Present

Output a clear design document:
- API spec (route, method, request/response shape)
- Schema diagram or table definitions
- Service interaction diagram if multiple services are involved
- Open questions or decisions the user should make

Do not write implementation code unless explicitly asked — the goal is a design the user can hand to `/coding`.
