---
name: security-review
description: Audit code or a diff for security vulnerabilities. Use when the user
  says "security review", "check for vulnerabilities", "audit this", "is this
  secure?", or before merging auth/API/input-handling changes.
---

# Security Review

Audit the target for security issues and produce a prioritized findings report.

## Read first

Before any other step:
- `.claude/docs/security.md`
- `.claude/docs/investigation-tools.md`

## Arguments

`$ARGUMENTS` is optional. If a PR number is given, review that PR's diff.
Otherwise review the current branch or the file/module specified.

## Gather the target

**Current branch:**
```bash
git diff --stat main...HEAD
git log main...HEAD --oneline
```

If `--stat` shows more than 10 changed files, proceed with the stat output only — do not fetch the full diff.
If 10 files or fewer, also run `git diff main...HEAD` to read the full diff.

**PR number:**
```bash
gh pr view $ARGUMENTS
gh pr diff $ARGUMENTS
```

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
