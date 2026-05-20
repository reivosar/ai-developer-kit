## Skill Dispatch

Every task must go through a skill — never handle any task inline.

### Implementation

- All coding (implementation against a known design) → `/coding`
- Locating the relevant code, entry point, or file before implementation → `/investigate`
- Bug / error / test failure investigation → `/troubleshooting`
- Frontend architecture/design (component design, state management, routing design) → `/frontend-design`
- Backend architecture/design (API design, DB model, service boundaries) → `/backend-design`
- Planning a multi-file feature or unfamiliar change → `/plan`
- Test generation or coverage improvement → `/test`
- Code simplification, quality review, or refactoring review → `/simplify`

### Understanding

- Explaining a function, file, or concept ("what does X do", "how does this work") → `/explain`
- Exploring an unfamiliar codebase or module ("overview of X", "where is Y handled") → `/explore`

### Git and versioning

- Committing → `/commit`
- Creating a pull request → `/pull-request`
- Reviewing a PR or branch → `/code-review`
- Worktree operations → `/worktree`

### Documentation and security

- Documentation (README, ADR, OpenAPI spec, inline comments) → `/documentation`
- Security audit or vulnerability review of pending changes → `/security-review`

### Kit and configuration

- Editing kit configuration (settings.json, hooks, permissions, env vars) → `/edit-kit`
- Updating docs and skills from the upstream kit → `/update-kit`
- Reducing permission prompts by allowlisting safe commands → `/fewer-permission-prompts`

### Feedback

- Filing a rule/skill gap or improvement insight → `/feedback`

### Catch-all

If no skill above clearly matches, invoke `/propose` — it will surface candidate skills to the user and let them choose how to proceed.
Never respond inline and never silently fall back to `/feedback` without user input.

### Notes

When to use `/coding` vs. a design skill: use a design skill when the structure or boundaries are undecided; use `/coding` once the design is settled and the task is implementation.

`/investigate` is for pre-implementation code location only (read-only). For bug investigation, use `/troubleshooting` — it internally calls `/investigate` as its first step. Never call `/investigate` standalone for debugging.
