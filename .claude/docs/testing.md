## Structure

Use Arrange-Act-Assert in every test:
- Arrange: set up inputs, mocks, and state
- Act: call the function or endpoint under test
- Assert: verify outputs and side effects

## Naming

`test_<function>_<scenario>_<expected_outcome>` — make the failure message self-explanatory without reading the body.

## What to Mock

Mock at system boundaries only:
- External HTTP APIs, payment gateways, email/SMS services → mock
- Internal DB in unit tests → mock the repository interface
- Internal DB in integration tests → use a real test database, never a mock
- Clock/time → inject; never call `Date.now()` or `time.Now()` directly in logic

Never mock the module under test. Never mock to make a test pass.

## Coverage Targets

- Critical paths (auth, payment, data mutation): 90%+ branch coverage
- Overall: 70%+ line coverage
- Coverage numbers are a floor, not a goal — a test that doesn't assert behavior doesn't count

## Test Types

Use the right type for each scenario:

| Type | When to use |
|---|---|
| Unit | Pure functions, business rules, isolated transformations |
| Integration | Service-to-DB, service-to-external-API boundary, message queue |
| E2E | Full user flows through the UI or public API surface |

Prefer unit tests for speed; add integration tests at every external boundary; limit E2E to the top 3–5 critical user journeys.

## Test Design Techniques

Apply these techniques when identifying what to test:

- **Equivalence Partitioning** — divide inputs into classes the system treats identically; write one test per class. For an age field accepting 0–120: test one value below 0, one in 0–120, one above 120.
- **Boundary Value Analysis** — test at and just beyond partition edges where defects cluster. For range [min, max]: test min-1, min, max, max+1.
- **Decision Table** — enumerate combinations of conditions and their expected actions in a table; use when rules involve multiple interdependent conditions.
- **State Transition** — model the system as states and events; cover every valid transition and at least one invalid transition per state.
- **Error Guessing** — add cases drawn from experience: empty string, null, zero, negative numbers, max int, Unicode edge cases, duplicate submissions.
- **Checklist-based** — maintain a reusable checklist of recurring concerns (auth boundaries, pagination edge cases, concurrent writes, timezone offsets); apply it to every new feature area.

## Python Testing Rules

All Python test files must use pytest — no exceptions, including hook test files under `.claude/hooks/`.

Prohibited patterns in Python tests:
- No custom harness scripts (global `passed`/`failed` counters)
- No `if __name__ == "__main__"` test runner blocks — pytest discovers and runs tests
- No `check()` or `run_test()` helper functions as a substitute for pytest assertions
- All test functions must follow the `test_<function>_<scenario>_<expected_outcome>` naming convention

Good:
```python
def test_is_allowed_command_with_git_status_returns_true():
    assert is_allowed_command("git status")
```

Bad:
```python
passed = 0
failed = 0

def check(condition, label):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
```

## Prohibited Patterns

- No snapshot tests — they fail on irrelevant changes and create false confidence
- No `expect(true).toBe(true)` or empty assertions
- No tests that pass when the implementation is deleted
- No `sleep`/`setTimeout` in tests — use proper async primitives or fake timers

## Execution

Run the full test suite after every implementation change. Do not call a task done until all tests pass.
