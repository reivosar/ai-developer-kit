---
name: skill-selector
description: Mandatory entry point for every task. Analyzes the request, classifies the intent, and dispatches to the correct skill. Never performs work directly.
---

# Skill Selector

Mandatory first step for every task. Classify the request and dispatch to the correct skill.

## Process

### Step 1: Extract the core intent

From the user's request, answer these three questions:

1. **Action** — what operation is requested? (implement, fix, explain, review, commit, document, configure, ...)
2. **Subject** — what is being acted on? (function, file, feature, bug, PR, concept, module, ...)
3. **Phase** — is the structure/design already decided, or does it need to be determined first?

### Step 2: Classify the request

Apply these classifiers in order — stop at the first match.

**Git / GitHub operations**
- Committing staged changes → `/commit`
- Opening a PR → `/pull-request`
- Reviewing a PR or branch → `/code-review`
- Worktree create/remove/list → `/worktree`

**Understanding requests** ("what does X do", "how does this work", "explain Y", "overview of Z")
- Single function, file, or concept → `/explain`
- Broad module, subsystem, or codebase area → `/explore`

**Failure or error investigation** (error message, failing test, unexpected behavior)
- Root cause unknown → `/troubleshooting`
- Known error; need to locate the relevant file/function before fixing → `/investigate` then `/troubleshooting`

**Pre-implementation code location** ("where is X defined", "which file handles Y" — read-only, no error present)
- → `/investigate`

**Design — structure or boundaries are not yet decided**
- Frontend: components, state, routing → `/frontend-design`
- Backend: API shape, DB model, service boundaries → `/backend-design`
- Multi-file feature with unclear structure → `/plan`

**Implementation — design is settled, task is to write code**
- Writing or changing implementation code → `/coding`
- Adding tests or improving coverage → `/test`
- Simplifying, refactoring, or quality review → `/simplify`

**Documentation or security**
- README, ADR, OpenAPI spec, inline comments → `/documentation`
- Auditing a diff or PR for vulnerabilities → `/security-review`

**Kit configuration**
- Editing `settings.json`, hooks, or permissions → `/edit-kit`
- Pulling upstream kit updates → `/update-kit`
- Reducing permission prompts → `/fewer-permission-prompts`

**Automation**
- Recurring or interval-based execution → `/loop`
- Scheduled one-off task → `/schedule`

**Feedback / API**
- Reporting a rule or skill gap → `/feedback`
- Claude API or Anthropic SDK questions → `/claude-api`

### Step 3: Resolve ambiguity

When two skills could match, apply the tie-breaking rule:

| Ambiguous pair | Tie-break |
|---|---|
| `/coding` vs. design skill | Design undecided → design skill; design settled → `/coding` |
| `/troubleshooting` vs. `/investigate` | Error/failure present → `/troubleshooting`; locating code only → `/investigate` |
| `/explain` vs. `/explore` | Single item → `/explain`; broad area → `/explore` |
| `/simplify` vs. `/coding` | Goal is quality/clarity → `/simplify`; goal is new behavior → `/coding` |

If still unclear after applying the tie-break, invoke `/propose`.

### Step 4: Invoke

Invoke the matched skill immediately with the original user request as arguments. No confirmation needed.

## Rules

- Never perform any work in this skill — always delegate
- Never ask for confirmation before invoking the matched skill
- Never skip this skill and go inline
