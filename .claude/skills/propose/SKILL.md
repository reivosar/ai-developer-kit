---
name: propose
description: Present the user with options when no other skill clearly fits the request. Ask clarifying questions, surface the closest matching skills, and let the user choose how to proceed. Never handle unmatched requests inline — always surface them here.
---

# Propose

Engage the user when no other skill clearly fits the request.

## When to invoke

- The request does not map cleanly to any skill in the dispatch table
- The intent is ambiguous across two or more skills
- The user's phrasing suggests a novel workflow not yet covered by any skill

## Step 1: Restate the request

In one sentence, restate what you understood the user to be asking. This confirms interpretation and gives the user an early chance to correct it.

## Step 2: Identify candidate skills

List up to three skills from the dispatch table in `/skill-selector` that partially match the request. For each, state in one clause what it covers and what it would miss for this request.

## Step 3: Ask the user to choose

Present the options as a numbered list and ask which direction to take:

1. Route to `/<skill>` — `<what that skill will do>`
2. Route to `/<skill>` — `<what that skill will do>`
3. Describe what you actually want — I will route or handle accordingly

Wait for the user's response before taking any action.

## Step 4: Route

Once the user selects an option or clarifies:
- If they pick a skill: invoke it immediately
- If they describe a new need: check the dispatch table in `/skill-selector` once more; if still no match, invoke `/feedback` to file a skill-gap issue before proceeding
