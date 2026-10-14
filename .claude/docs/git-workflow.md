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

The user merges and closes pull requests. The agent opens them and never merges into `main`: `pre-bash.py` blocks `gh pr merge`, `gh pr close`, `git push` while on `main`, and `git merge` or `git pull` of any branch other than `main`.

PR body: follow the project's pull request template, or `.claude/templates/github/PULL_REQUEST_TEMPLATE.md` when the project has none. See Pull Request and Issue Content below.

Merge requirements:
- At least 1 approval (2 for changes to auth, payments, or data migrations)
- All CI checks passing
- No unresolved review comments

## Merge Strategy

- **Default: squash and merge** — one commit per PR on `main`; keeps history linear
- **Exception: merge commit** — for release branches or when commit history detail matters
- **Never rebase `main` onto a feature branch** — only rebase feature branches onto `main`
- Force push is forbidden on every branch for the agent: the allow list has no form of it, and `pre-bash.py` blocks `--force` on every git command

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

## Versioning

- Semantic versioning: `MAJOR.MINOR.PATCH`
- Version is determined by Conventional Commits types: `feat` → minor, `fix` → patch, `BREAKING CHANGE` → major
- Tag releases on `main` after merging the release branch: `git tag v2.3.0`
- Maintain a `CHANGELOG.md`; update it as part of the release PR

## Pull Request and Issue Content

The templates in `.claude/templates/github/` hold the sections a body must have. Each section comes from a source below, not from habit. A section marked optional may be deleted from a body; every other section must be filled. `template_guard.py` blocks `gh pr create`, `gh pr edit`, `gh issue create`, and `gh issue edit` when a required section is missing or a section is left empty. A project's own templates under `.github/` take the place of the kit's pull request template and are accepted beside the kit's issue templates.

| Template | Section | Source |
|---|---|---|
| Pull request | What | [1]: a description communicates "What change is being made?" |
| Pull request | Why, with `Closes #N` | [1]: "Why are these changes being made?"; [2]: reviewers name understanding the reason of a change as the hardest part of a review; [3] |
| Pull request | Verification | [4]: a reviewer asks for tests appropriate for the change; [5]: Testing, Any Relevant Logs or Outputs |
| Pull request | Breaking changes | [5]: Does This Introduce a Breaking Change?; [6] |
| Pull request | Known limits (optional) | [1]: "If there are any shortcomings to the approach, they should be mentioned." |
| Pull request | Review focus (optional) | [7]: where reviewers should pay special attention |
| Bug report | Steps to reproduce | [8]: the item developers rate most important (83%), and errors in it are the most severe problem (79%); [10] |
| Bug report | Expected result, Actual result | [9]: "Expected results and actual results"; [10] |
| Bug report | Evidence | [8]: stack traces (57%) and test cases (51%) come next in importance; [9]: logs, screenshots, recordings |
| Bug report | Version and environment | [9]: "Identification of the test object and test environment"; [8]: a wrong version number misleads (22%); [10] |
| Bug report | Impact and workaround (optional) | [9]: severity. Optional because developers rate severity 0% for fixing a bug [8] |
| Feature request | Problem | [11]: who wants it, what they want, and why; [12]: a request always describes the problem (SC3.4) and holds one requirement (SC3.7) |
| Feature request | Acceptance criteria | [13]: given a context, when an event occurs, then outcomes follow; [14]: an outcome is an observable output |
| Feature request | Proposed solution (optional) | [12]: a request may include hints for a solution (SC3.4) |
| Feature request | Related issues (optional) | [12]: duplicates are linked (SC3.9) and links say how the requests relate (SC3.10) |

Left out on purpose: risk and rollback (no primary source or study was found for it); the "As a, I want, so that" sentence form ([11] calls it training wheels that people outgrow); identifier, date, and status (the tracker records them [9]); priority (a project sets it with its own labels).

Sources, each opened and read when this section was written (October 2026):

1. Google Engineering Practices, "Writing good CL descriptions" — <https://google.github.io/eng-practices/review/developer/cl-descriptions.html>
2. Bacchelli and Bird, "Expectations, Outcomes, and Challenges of Modern Code Review", ICSE 2013 — <https://sback.it/publications/icse2013.pdf>
3. GitHub Docs, "Linking a pull request to an issue" — <https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue>
4. Google Engineering Practices, "What to look for in a code review" — <https://google.github.io/eng-practices/review/reviewer/looking-for.html>
5. Microsoft Engineering Fundamentals Playbook, "Pull Request Template" — <https://microsoft.github.io/code-with-engineering-playbook/code-reviews/pull-request-template/>
6. Conventional Commits 1.0.0 — <https://www.conventionalcommits.org/en/v1.0.0/>
7. GitHub Docs, "Helping others review your changes" — <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/getting-started/helping-others-review-your-changes>
8. Zimmermann et al., "What Makes a Good Bug Report?", IEEE Transactions on Software Engineering 36(5), 2010 — <https://thomas-zimmermann.com/publications/files/zimmermann-tse-2010.pdf>
9. ISTQB Certified Tester Foundation Level Syllabus v4.0.1, section 5.5 — <https://www.istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf>
10. Mozilla, "Bug Writing Guidelines" — <https://bugzilla.mozilla.org/page.cgi?id=bug-writing.html>
11. Agile Alliance, "User Story Template" — <https://www.agilealliance.org/glossary/user-story-template/>
12. Heck and Zaidman, "A Quality Framework for Agile Requirements: A Practitioner's Perspective" — <https://ar5iv.labs.arxiv.org/html/1406.4692>
13. Dan North, "Introducing BDD" — <https://dannorth.net/blog/introducing-bdd/>
14. Cucumber, "Gherkin Reference" — <https://cucumber.io/docs/gherkin/reference/>
