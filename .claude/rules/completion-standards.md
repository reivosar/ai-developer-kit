## Completion Standards

All work is subject to verification by a strict follow-up audit. Every completion
report must satisfy the criteria below without exception.

### Mandatory requirements

**Read the full context.**
Do not judge by diff alone. Always read the surrounding code to identify the actual
impact scope before making any change or claim.

**Build on verified facts.**
Do not proceed based on guesses. Do not treat unverified assumptions as facts.

**Confirm actual behavior.**
Run the code, execute the tests, or otherwise verify the outcome directly. Do not
declare work complete until success is observed — not inferred.

**Identify root causes from evidence.**
When an error occurs, trace it through logs and facts. Do not assert a cause without
evidence.

### Absolute prohibitions — instant rejection

**False reporting.** Do not review or describe code you have not read as if you had.

**Ungrounded assertions.** Do not state "this works" or "no issues" without a test
or verification step to back it.

**Skipped investigation.** Do not substitute a quick guess for proper root-cause
analysis. If the cause is unknown, say so and investigate.

**Fake completion.** A TODO comment or a stub is not a completed implementation.
Do not mark work done while placeholders remain.

**Superficial merge approval.** Do not approve or declare a large diff complete
without inspecting every changed file. Visual confirmation of details is required.

### Reporting

When reporting completion, state explicitly:
- What verification was performed (command run, output observed, test result)
- What the verified outcome was (pass/fail, observed behavior)

Omit this and the report is invalid.
