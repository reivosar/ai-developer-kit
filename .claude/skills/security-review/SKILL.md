---
name: security-review
description: Audit code or a diff for security vulnerabilities. Use when the user
  says "security review", "check for vulnerabilities", "audit this", "is this
  secure?", or before merging auth/API/input-handling changes.
---

# Security Review

Audit the target for security issues and produce a prioritized findings report.

## Setup

Before gathering the diff:
- `.claude/docs/security.md`
- `.claude/docs/investigation-tools.md`
- `.claude/docs/diff-strategy.md`

## Arguments

`$ARGUMENTS` is optional. If a PR number is given, review that PR's diff.
Otherwise review the current branch or the file/module specified.

## Gather the target

**Current branch:** use the **diff-branch** command from `commands.md`.

Apply the threshold from `.claude/docs/diff-strategy.md`:
use the **diff-branch-files** command from `commands.md`.

**PR number:** use the **pr-diff** command from `commands.md` (pass `$ARGUMENTS` as `$PR`).

Apply the threshold from `.claude/docs/diff-strategy.md`:
use the **pr-diff-files** command from `commands.md` (pass `$ARGUMENTS` as `$PR`).

**File or module:** read the file directly.

## Review areas

### Injection
- SQL injection, command injection, XSS, SSRF, path traversal
- Any place user input or external data is concatenated into a query, command, or path

### Authentication & authorization
- Missing auth checks on endpoints or functions
- Privilege escalation: can a lower-privilege actor reach a higher-privilege path?
- Insecure direct object references

### Secrets & configuration
- API keys, passwords, or tokens hardcoded in source
- Secrets logged or included in error messages
- Environment variables not validated at startup

### Data handling
- Sensitive data returned to clients that should not receive it
- Missing input validation at trust boundaries (user input, external APIs, env vars)
- Insecure deserialization

### Dependencies
- Calls to known-vulnerable functions or deprecated APIs

## Report format

One finding per item: **severity** (Critical / High / Medium / Low), file:line,
description, and recommended fix.

Omit severity levels with no findings.

End with a verdict:
- **Clear** — no security issues found
- **Review required** — findings that must be addressed before merge
- **Informational** — findings worth knowing but not blocking
