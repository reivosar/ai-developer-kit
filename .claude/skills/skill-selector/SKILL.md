---
name: skill-selector
description: Optional auxiliary skill for ambiguous dispatch. Use when the correct skill from skill-dispatch.md is unclear. For unambiguous tasks, consult skill-dispatch.md directly and invoke the matching skill without this step.
---

# Skill Selector

Auxiliary skill for dispatch when the correct skill is unclear. If the task maps clearly
to a skill in `skill-dispatch.md`, invoke that skill directly — do not use this.

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
