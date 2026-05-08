---
name: frontend
description: Frontend coding skill for creating UI components, fixing frontend bugs, and implementing frontend features. Use this skill whenever the task involves HTML, CSS, JavaScript, TypeScript, React, Vue, Svelte, or any other frontend framework — whether it's building something new, fixing a bug, or modifying existing UI. Trigger this skill for anything that runs in the browser or affects what the user sees.
---

# Frontend

Implement or fix frontend code with a focus on correctness, accessibility, and maintainability.

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

- Identify the framework and version in use (`package.json`, `vite.config.*`, `next.config.*`, etc.)
- Find the relevant component or entry point — search by filename or symbol, don't read speculatively
- For bug fixes: reproduce the problem in your head by tracing props/state through the render path

### 2. Plan the change

State in one sentence what you're going to build or fix. For new components:
- Where does it live in the component tree?
- What props does it accept?
- What state does it manage locally vs. lifting to the parent?

For bug fixes: state the root cause before touching code.

### 3. Implement

- Match the existing style: spacing, naming conventions, component structure
- Handle edge cases visible to the user: empty states, loading, error boundaries
- Keep accessibility in mind: semantic HTML, keyboard navigation, ARIA where needed
- Do not refactor unrelated code — scope changes tightly

### 4. Verify

- Check for TypeScript errors if applicable
- Run existing tests; write a minimal test if none exist for the changed path
- If a dev server is running, verify the golden path visually

## Report

When done:
- **What changed**: component(s) affected and the nature of the change
- **Why**: the design decision or root cause
- **Edge cases handled**: empty/loading/error states, accessibility considerations
