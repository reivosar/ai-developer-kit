---
name: standup
description: Generate a standup report from recent git history. Use this skill when the user asks for a standup, daily update, status summary, or says "what did I work on?", "summarize my recent work", or "help me write my standup."
---

# Standup

Generate a standup report from git history.

## Gather recent commits

```bash
git log --since="2 days ago" --oneline --author="$(git config user.name)"
```

If the result is sparse (e.g. Monday morning), extend the window:

```bash
git log --since="5 days ago" --oneline --author="$(git config user.name)"
```

Also check for any open branches with uncommitted or unpushed work:

```bash
git branch -v
```

## Write the report

**Format:**
```
Yesterday
- <what was accomplished, in plain language>

Today
- <planned work based on open branches or stated next steps; "TBD" if nothing is clear>

Blockers
- <anything blocking progress; "None" if clear>
```

**Writing guidance:**
- Translate commit messages into what was *achieved*, not just what was changed. "Fixed null pointer in payment flow" is better than "fix: null check in PaymentService.java".
- Group related commits into a single bullet if they represent one coherent piece of work.
- Keep each bullet to one line. The standup is a signal, not a report.
- If there are no commits (e.g. research day, meetings, reviews), ask the user what they worked on before generating.
