---
name: frontend-design
description: Design and implement frontend features. Use this skill when the user wants to build or redesign UI components, pages, or frontend features — whether from scratch or modifying existing ones.
---

# Frontend Design

## Setup

Always read:
- `.claude/docs/frontend.md`
- `.claude/docs/coding.md`
- `.claude/docs/code-style.md`

Read only when the task explicitly involves:
- Auth, form validation, or external data handling → `.claude/docs/security.md`
- A design system, token library, or shared component library → `.claude/docs/design-system.md`

Do not read a conditional file unless the task description or codebase investigation confirms it applies.

## Steps

### 1. Investigate

Understand the existing codebase before touching anything:
- Identify the framework, tooling, and directory structure
- Find components or pages adjacent to the target area
- Note the styling approach, naming conventions, and state management patterns in use

### 2. Design

Decide the structure before writing code:
- Component breakdown: what components are needed and their responsibilities
- State ownership: what is local vs. shared
- Data flow: props down, events up, or external state
- Edge cases to handle: loading, empty, error states

State the design in a short summary before implementing.

### 3. Implement

Write the code following the conventions from the rule files. Match the existing codebase style exactly — do not introduce new patterns without reason.

### 4. Verify

- Check for type errors if TypeScript is in use
- Run existing tests; add a test for the changed path if none exist
- Confirm the main flow and at least one edge case work correctly
