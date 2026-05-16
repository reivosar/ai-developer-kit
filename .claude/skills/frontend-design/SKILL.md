---
name: frontend-design
description: Design and implement frontend features. Use this skill when the user wants to build or redesign UI components, pages, or frontend features — whether from scratch or modifying existing ones.
---

# Frontend Design

## Setup

Always read:
- `.claude/docs/git-workflow.md`
- `.claude/docs/frontend.md`
- `.claude/docs/coding.md`
- `.claude/docs/code-style.md`

Read only when the task explicitly involves:
- Auth, form validation, or external data handling → `.claude/docs/security.md`
- A design system, token library, or shared component library → `.claude/docs/design-system.md`

Do not read a conditional file unless the task description or codebase investigation confirms it applies.

## Steps

### 1. Investigate

Invoke /investigate. Note the styling approach, naming conventions, and state management patterns in use.

### 2. Design

Decide the structure before writing code:
- Component breakdown: what components are needed and their responsibilities
- State ownership: what is local vs. shared
- Data flow: props down, events up, or external state
- Edge cases to handle: loading, empty, error states

State the design in a short summary before implementing.

### 3. Implement

Invoke /coding with the design from Step 2. /coding handles implementation, review, commit, and PR.
