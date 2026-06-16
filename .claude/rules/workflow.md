## Workflow

### Step compliance over context minimization

Context minimization never justifies skipping a mandated workflow step.
Mandatory steps — /simplify --auto (Refactor), /code-review, /commit —
must execute regardless of context cost.
If a step requires loading a file or invoking a skill, do it. Omitting it to save tokens
is a violation, not an optimization.

### Sequencing

- When the next step is unambiguous, invoke the appropriate skill immediately without asking for prior confirmation; reserve pre-action confirmation for destructive or irreversible operations only
- After committing on a feature branch, immediately invoke `/pull-request` — do not wait for the user to ask
- When `/code-review` returns issues, fix them immediately and re-invoke `/code-review`; repeat until the verdict is Approved — never stop after a "Changes requested" verdict and present it to the user
