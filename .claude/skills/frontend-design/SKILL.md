---
name: frontend-design
description: Frontend design skill for planning and designing UI architecture, component structure, state management strategy, and UX patterns. Use this skill when the task involves designing how a frontend feature should be structured — component hierarchy, data flow, routing, styling approach — before or instead of writing code. Trigger for frontend architecture decisions, design reviews, or "how should we build this UI?" questions.
---

# Frontend Design

Design the structure, architecture, and approach for frontend work before implementation begins.

## Setup

Read the following rule files before proceeding:
- `.claude/rule-library/code-style.md`

## Arguments

The design goal or question is passed as `$ARGUMENTS`. If existing code is relevant, read it first.

## Process

### 1. Understand the requirement

Before proposing anything:

- Clarify what the user is trying to build and why
- Identify constraints: existing framework, design system, performance requirements, accessibility needs
- Check what already exists in the codebase that's relevant

### 2. Design

Produce a concrete design covering:

- **Component structure**: what components exist, their responsibilities, hierarchy
- **Data flow**: where state lives, how it flows down (props) or up (callbacks/events)
- **Routing**: if applicable, how pages/views are organized
- **Styling approach**: CSS modules, Tailwind, styled-components, etc. — match what's in use
- **Edge cases**: loading, empty, error states for each key component

### 3. Present

Output a clear design document:
- Component tree (ASCII or list form)
- Props interface for each component
- State ownership decisions with rationale
- Any open questions or tradeoffs the user should decide

Do not write implementation code unless explicitly asked — the goal is a design the user can hand to `/coding`.
