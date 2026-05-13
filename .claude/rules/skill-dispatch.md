## Skill Dispatch

Every task must go through a skill — never handle any task inline.

### Implementation

- All coding (implementation against a known design) → `/coding`
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
- Customizing keyboard shortcuts or keybindings → `/keybindings-help`
- Initializing a new CLAUDE.md for a project → `/init`

### Automation

- Recurring or interval-based tasks ("run this every N minutes") → `/loop`
- Scheduled one-off or cron-based remote tasks → `/schedule`

### Feedback and API

- Filing a rule/skill gap or improvement insight → `/feedback`
- Questions or implementation involving the Claude API or Anthropic SDK → `/claude-api`

### Catch-all

If no skill above clearly matches, pick the closest one and invoke it.
Never respond inline — if genuinely no skill fits, invoke `/feedback` to file a skill-gap issue.

### Notes

When to use `/coding` vs. a design skill: use a design skill when the structure or boundaries are undecided; use `/coding` once the design is settled and the task is implementation.

`.claude/docs/` is not auto-loaded — each skill reads only the rule files it needs. Once a rule file has been read in a session, never read it again — treat it as cached.
