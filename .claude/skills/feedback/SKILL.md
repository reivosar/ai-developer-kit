---
name: feedback
description: Capture a rule gap, skill gap, or new pattern discovered during project work and file it as a GitHub issue on the ai-developer-kit repository. Use this skill when you notice something missing from the kit's rules or skills, want to suggest an improvement, or the user says "this should be a rule", "add this to the kit", "file this as feedback", or "log this insight."
---

# Feedback

File an improvement insight as a GitHub issue on `reivosar/ai-developer-kit`.

## Arguments

`$ARGUMENTS` is the insight description. If empty, ask the user:
1. What was missing or should be improved?
2. In which project / what task did this come up?
3. What change would address it (optional)?

## Step 1: Determine category

Choose one label based on the insight:

| Label | When to use |
|---|---|
| `rule-gap` | A rule file lacks guidance that caused confusion or a mistake |
| `skill-gap` | A skill's process was incomplete or missing a step |
| `new-pattern` | A repeating pattern not yet captured as a rule or skill |
| `enhancement` | An existing rule or skill works but could be clearer or stronger |

## Step 2: Derive the issue title

- Imperative, under 72 characters
- Include the affected area: `rule(security):`, `skill(coding):`, `rule(logging):`, etc.
- Example: `rule(errors): add guidance for retrying non-idempotent operations`

## Step 3: Create the issue

```bash
gh issue create \
  --repo reivosar/ai-developer-kit \
  --title "<title>" \
  --label "<label>" \
  --body "$(cat <<'EOF'
## Insight

<What was missing or should be improved>

## Context

Project: <project name or path>
Task: <what was being worked on when this was noticed>

## Suggested change

<Which file to change and what to add or modify — leave blank if unknown>
EOF
)"
```

## Step 4: Report

Output the issue URL.
