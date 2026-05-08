---
name: coding
description: General-purpose coding skill for tasks that don't clearly belong to frontend or backend — CLI tools, scripts, full-stack changes, shared utilities, configuration, build tooling, or anything cross-cutting. Also use this as a fallback when the domain is ambiguous. Handles new feature creation, bug fixes, and light design decisions. If you're unsure whether to use /frontend, /backend, or /coding, use /coding.
---

# Coding

Implement or fix code for general-purpose, cross-cutting, or ambiguous tasks.

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

- Identify the language, toolchain, and conventions in use
- Locate the relevant entry point or file — search by symbol or filename, don't read speculatively
- For bug fixes: trace the execution path to the failure and state the root cause first
- For new work: clarify ambiguous requirements before writing code

### 2. Plan the change

State in one sentence what you're going to build or fix. Consider:
- What does this change affect?
- What are the inputs and outputs?
- What are the failure modes?

### 3. Implement

- Match the existing code style and conventions
- Validate inputs at system boundaries
- Keep the change tightly scoped — do not refactor unrelated code
- Write the simplest correct solution; avoid over-engineering

### 4. Verify

- Run existing tests; write a focused test for the changed path if none exist
- Confirm the happy path and at least one error path

## Report

When done:
- **What changed**: files/functions affected
- **Why**: the design decision or root cause
- **Caveats**: anything the caller should know about edge cases or follow-up work
