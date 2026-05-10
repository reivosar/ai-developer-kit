## Skill Dispatch

Always invoke the corresponding skill — never handle these tasks inline:

- All coding (implementation against a known design) → `/coding`
- Bug / error / test failure investigation → `/troubleshooting`
- Creating a pull request → `/pull-request`
- Reviewing a PR or branch → `/code-review`
- Frontend architecture/design (component design, state management, routing design) → `/frontend-design`
- Backend architecture/design (API design, DB model, service boundaries) → `/backend-design`
- Planning a multi-file feature → `/plan`
- Committing → `/commit`
- Worktree operations → `/worktree`
- Documentation (README, ADR, OpenAPI spec) → `/documentation`
- Filing a rule/skill gap or improvement insight → `/feedback`
- Updating rule-library and skills from the upstream kit → `/update-kit`
- Editing kit configuration (settings.json, hooks, permissions) → `/edit-kit`

When to use `/coding` vs. a design skill: use a design skill when the structure or boundaries are undecided; use `/coding` once the design is settled and the task is implementation.

`.claude/rule-library/` is not auto-loaded — each skill reads only the rule files it needs. Once a rule file has been read in a session, never read it again — treat it as cached.
