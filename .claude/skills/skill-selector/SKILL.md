---
name: skill-selector
description: Mandatory entry point for every task. Reads the user's request, matches it against skill-dispatch.md, and invokes the correct skill. Never performs work directly.
---

# Skill Selector

Entry point for every task. Dispatch to the correct skill — never perform any work inline.

## Setup

Always read:
- `.claude/rules/skill-dispatch.md`

## Process

### Step 1: Read the request

Identify what the user wants to do. One sentence.

### Step 2: Match to a skill

Compare the request against every entry in `skill-dispatch.md`. Select the single best match.

### Step 3: Invoke

Invoke the matched skill immediately. Pass the original user request as arguments.

If no skill clearly matches, invoke `/propose`.

## Rules

- Never perform any work in this skill — always delegate
- Never ask for confirmation before invoking the matched skill
- Never skip this skill and go inline
