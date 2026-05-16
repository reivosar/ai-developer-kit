## Branch Naming

Format: `<type>/<short-description>` using kebab-case

| Type | When to use | Example |
|---|---|---|
| `feat/` | New feature or capability | `feat/user-email-verification` |
| `fix/` | Bug fix | `fix/login-redirect-loop` |
| `hotfix/` | Emergency production fix | `hotfix/payment-timeout-crash` |
| `refactor/` | Code restructure with no behavior change | `refactor/extract-auth-middleware` |
| `docs/` | Documentation only | `docs/api-authentication-guide` |
| `chore/` | Tooling, dependencies, CI | `chore/upgrade-node-20` |
| `release/` | Release preparation | `release/v2.3.0` |

- Max 50 characters total; use hyphens, not underscores
- Reference the issue/ticket number if applicable: `fix/123-login-redirect-loop`

## Commit Guards

- Never commit directly to `main` — always branch first
- The branch must correspond to the current task; if on an unrelated branch, return to `main` and cut a new one
- Do not stage unstaged files without explicit user request
- After a successful commit on a feature branch, immediately open a PR — do not wait for the user to ask

## Commit Messages

Follow Conventional Commits format: `<type>(<scope>): <subject>`

- `feat`: new feature (triggers minor version bump)
- `fix`: bug fix (triggers patch version bump)
- `docs`: documentation only
- `refactor`: code change without behavior change
- `test`: adding or correcting tests
- `chore`: tooling, dependencies, CI/CD changes
- `perf`: performance improvement
- `BREAKING CHANGE`: footer note for incompatible API changes (triggers major version bump)

Subject line rules:
- Imperative mood: `"add user login"` not `"added"` or `"adding"`
- 72 characters max
- No period at end
- If a body is needed, separate from subject with a blank line

## Pull Request Workflow

1. Open a draft PR early to signal work-in-progress; remove draft when ready for review
2. Self-review the diff (`git diff main...HEAD`) before requesting review
3. Assign at least one reviewer; for security or data changes, assign two
4. Resolve all review comments before merging; do not dismiss without addressing
5. Delete the branch immediately after merge
6. Never force-push on diverged history — report the conflict to the user instead

PR body structure (required):

```
## What
<1-3 bullets describing what changed>

## Why
<the motivation: what problem this solves or what requirement it fulfills>

## How to test
<concrete steps a reviewer can follow to verify the change works>
```

Merge requirements:
- At least 1 approval (2 for changes to auth, payments, or data migrations)
- All CI checks passing
- No unresolved review comments

## Merge Strategy

- **Default: squash and merge** — one commit per PR on `main`; keeps history linear
- **Exception: merge commit** — for release branches or when commit history detail matters
- **Never rebase `main` onto a feature branch** — only rebase feature branches onto `main`
- Force push is forbidden on `main`; permitted on personal feature branches only

## Branch Lifecycle

- Feature branches live no longer than 3 days; split the work if it takes longer
- Delete merged branches immediately; stale branches are pruned weekly
- Never reuse a branch name after it has been merged

## Emergency Hotfix Procedure

1. Branch from `main` (not a feature branch): `git checkout -b hotfix/<description> main`
2. Apply the minimal fix — no unrelated changes
3. Open a PR marked `[HOTFIX]`; requires 1 approval (on-call engineer)
4. Merge immediately after approval; deploy to production
5. Back-merge `main` into any open long-running branches

## Worktrees

Use a git worktree when:

- Starting any implementation task that modifies files
- A critical bug needs fixing while mid-feature (keeps the feature branch clean)
- Running parallel review (fresh context, no anchoring bias)
- Trying a risky experiment that may be discarded
- Giving subagents isolated working copies

Cleanup behavior:

| Situation | Action |
|---|---|
| PR merged | Remove worktree and delete local branch |
| No changes made | Branch and directory deleted automatically |
| Changes present | Prompt to keep or delete |

Add `.claude/worktrees/` to `.gitignore` to keep worktree contents out of the main repo's untracked file list.

If a worktree needs gitignored files (e.g. `.env`), list them in a `.worktreeinclude` file at the project root — they will be copied automatically on worktree creation.

## Versioning

- Semantic versioning: `MAJOR.MINOR.PATCH`
- Version is determined by Conventional Commits types: `feat` → minor, `fix` → patch, `BREAKING CHANGE` → major
- Tag releases on `main` after merging the release branch: `git tag v2.3.0`
- Maintain a `CHANGELOG.md`; update it as part of the release PR
