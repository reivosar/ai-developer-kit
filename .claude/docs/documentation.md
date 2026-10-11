## README

Every project and every top-level service/package must have a `README.md` with these sections:
- **Overview**: one paragraph on what this is and why it exists
- **Setup**: exact commands to install dependencies and run locally
- **Usage**: key entry points, common commands, example requests
- **Architecture decisions**: link to ADR files or a brief rationale for non-obvious choices

Keep README accurate — a wrong README is worse than no README.

## Architecture Decision Records (ADR)

Use ADR format for any significant decision (framework choice, data model, external service, security approach):

```text
# NNN: Title

## Status
Proposed | Accepted | Deprecated | Superseded by NNN

## Context
What problem prompted this decision? What constraints existed?

## Decision
What was decided?

## Consequences
What becomes easier? What becomes harder? What is now assumed?
```

Store ADRs in `docs/adr/NNN-short-title.md`. Never delete them — mark as Superseded if replaced.

## Code Comments

- Comment the WHY, never the WHAT — the code already shows what it does
- Acceptable: hidden constraints, non-obvious invariants, workarounds for specific bugs, surprising behavior
- Not acceptable: paraphrasing the code, referencing ticket numbers, describing the caller

## API Documentation

- Every HTTP API must have an OpenAPI (Swagger) spec
- Keep the spec co-located with the code (e.g., `openapi.yaml` in the service root)
- Generate docs from the spec, not by hand — hand-written docs drift
- Document all error responses, not just success cases

## Document Length

- Every Markdown document stays within 200 lines; when one would exceed it, split it by responsibility into a separate document and link the two
- `doc_length_guard.py` blocks a write or edit that takes a Markdown document past the limit; an edit that shortens an oversized document is allowed, so it can be trimmed in steps
- The guard is off while the environment variable `DOC_LENGTH_GUARD_DISABLE` is set; use it only for a document that must grow without bound, such as a changelog

## Co-location

- Keep docs next to the code they describe — not in a separate wiki or repo
- Wikis go stale; co-located docs are updated with the code in the same PR
