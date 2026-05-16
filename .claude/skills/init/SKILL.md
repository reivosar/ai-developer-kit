---
name: init
description: Create a CLAUDE.md file for the current project. Use when the user
  says "init", "initialize", "create a CLAUDE.md", or "set up Claude Code for
  this project."
---

# Init

Create a CLAUDE.md that gives Claude accurate, project-specific guidance.

## Setup

Read `.claude/docs/git-workflow.md` before proceeding.

## Arguments

`$ARGUMENTS` is optional context (e.g. "this is a Go API server").

## Process

### 1. Explore the project

Run in a single parallel batch:
```bash
ls
find . -name "*.json" -maxdepth 2 -not -path "*/node_modules/*"
find . -name "*.toml" -maxdepth 2
find . -name "Makefile" -maxdepth 2
find . -name "*.mod" -maxdepth 2
```

Also read: README.md (if present), package.json / go.mod / pyproject.toml (if present).

Identify:
- Language and framework
- How to install dependencies, run tests, and build
- Top-level directory structure and what each area owns
- Any non-obvious conventions or constraints

### 2. Draft CLAUDE.md

Use this template:

```markdown
# CLAUDE.md

## Project

<One sentence: what this project does and its primary language/framework.>

## Commands

- Install: `<command>`
- Test: `<command>`
- Build: `<command>`
- Lint: `<command>` (if applicable)

## Architecture

<3-5 bullets describing the top-level directory structure and responsibilities.>

## Conventions

<Non-obvious rules a developer must follow. Omit anything obvious from the language/framework.>
```

### 3. Present and confirm

Show the draft. Ask: "Does this look right, or should I adjust anything?"
Do not write the file until the user approves.

### 4. Write

Write to `CLAUDE.md` in the project root using the Write tool.

### 5. Commit

Invoke /commit.
