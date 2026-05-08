---
name: backend
description: Backend coding skill for creating APIs, services, database models, fixing backend bugs, and implementing server-side features. Use this skill whenever the task involves server-side code — Node.js, Python, Go, Java, Ruby, databases, REST/GraphQL APIs, background jobs, or infrastructure-adjacent code. Trigger for anything that runs on the server, whether it's new feature work or a bug fix.
---

# Backend

Implement or fix backend code with a focus on correctness, security, and maintainability.

## Setup

Read the following rule files before proceeding:
- `.claude/rule-library/code-style.md`
- `.claude/rule-library/testing.md`
- `.claude/rule-library/security.md`

## Arguments

The task description is passed as `$ARGUMENTS`. If files are mentioned, read them first.

## Process

### 1. Understand the context

Before writing anything:

- Identify the language, framework, and runtime (`package.json`, `go.mod`, `pyproject.toml`, etc.)
- Locate the relevant handler, service, or model — search by symbol or route, don't read speculatively
- For bug fixes: trace the request path from entry point to the failure and state the root cause first

### 2. Plan the change

State in one sentence what you're going to build or fix. For new endpoints or services:
- What does this expose, and to whom?
- What data does it read or write?
- What are the error/failure modes?

For bug fixes: confirm the root cause before touching code.

### 3. Implement

- Match existing code style and conventions
- Validate all inputs at system boundaries — never trust external data
- Return appropriate status codes and error messages; never leak internals
- Use transactions where multiple writes must be atomic
- Do not refactor unrelated code — keep changes tightly scoped

### 4. Verify

- Run existing tests; write a focused integration or unit test for the changed path if none exist
- Check for obvious security issues: injection, over-permissive access, missing auth checks
- Confirm the happy path and at least one error path behave correctly

## Report

When done:
- **What changed**: the endpoint, service, or model affected
- **Why**: the design decision or root cause
- **Security considerations**: input validation, auth, data exposure handled
