# Coding Rules

## What These Rules Protect

Every rule in this file serves one goal: keep the cost of a change small, so that a failure can be fixed quickly and one fix does not break something else. The goal is the same in every language and framework; only the means differ. A change is cheap when two things hold:

- **The place to change can be identified** — from the words of a request or from the symptom of a failure, the code to change is found quickly and completely
- **The impact stays local** — a change affects only the code it touches

A unit that changes for one kind of reason serves both: it is easy to find, and a change to it does not spread. When two rules conflict, or a rule does not fit the case, choose the option that keeps the change cheaper by these two measures.

Two kinds of reader work on this code. A person learns the structure once and remembers it. An AI agent starts every session without memory and locates code by text search. Where a convention helps one reader and costs the other, keep the property and choose a means both can follow: explicit over inferred, direct over indirect, one place over many.

## Dependency Injection

- Every dependency (database, external service, logger, clock, config) is injected from outside — never instantiated inside a function or class
- A function or class that creates its own dependencies cannot be tested without side effects
- Inject at the construction boundary: pass dependencies through constructors or function parameters — not via globals or module-level singletons
- Wire dependencies in explicit code at one composition root, where each concrete type is named. When the project's framework supplies a container (Spring, NestJS), use its standard constructor injection with explicit types; do not add resolution by string key, naming convention, or custom reflection — the call target must be findable by reading the wiring
- Express an injected dependency as an interface where a second implementation exists or a test needs a fake: the system boundaries — database, external service, clock. Do not create an interface for a type that has one implementation inside the system; depend on the concrete type and call it directly

## Testable Structure

- Write code so it can be tested without real infrastructure (no live DB, no network, no file system) by default
- Pure functions — same input always produces same output, no side effects — are the easiest to test; prefer them for business logic
- Side effects (I/O, state mutation, external calls) are isolated at the edges of the system and injected, not embedded in logic
- If a unit of code cannot be tested without spinning up a server or a database, it has too many responsibilities — split it
- Avoid global state and module-level initialization that runs at import time; both make tests order-dependent and fragile

## State and Logic Separation

- **Logic** is a pure transformation: same inputs always produce same outputs, no reads or writes to external state
- **State** is data that changes over time: DB records, caches, session values, queues
- Never embed logic in state containers; never embed state mutation in logic functions
- Good: `calculate_discount(items, promo_code)` (pure logic) called separately from `save_order(order)` (state mutation)
- Bad: `process_order(items, promo_code)` that computes the discount AND writes to the database in one body
- If the caller is the only place that knows WHEN to mutate state, push the decision outward — keep the logic layer free of side effects

## Single Responsibility

- A function does one thing; if you need "and" to describe what it does, split it
- A module owns one concept; if it changes for two different reasons, split it
- Orchestration (calling A then B then C) is a separate concern from logic (what A, B, C each do)
- An orchestrating function contains only calls to other functions — no inline logic mixed in; if it does, split the logic into a named function
- If a function body needs a comment to divide it into sections, those sections are separate functions waiting to be extracted
- A function that mixes two or more of the following must be split immediately: (1) **Reading** — fetch, load, query, read data from anywhere; (2) **Judgment** — validate, decide, compare, compute a result; (3) **Side effects** — save, send, write, mutate, dispatch. Name each extracted piece for the single thing it does.

## Explicit Over Implicit

- Make dependencies, side effects, and failure modes visible in the function signature
- A function that can fail returns an error or throws a typed exception — it does not silently return null or swallow the error
- Configuration and environment values are passed in, not read from environment variables buried in logic
- Magic — behavior that changes based on hidden global state — is a bug waiting to happen

## Boundaries and Contracts

- Validate data at the entry boundary of each layer; trust data that has already been validated within the same layer
- The contract between layers is the type/interface — if the type is correct, the implementation can change freely
- Do not leak internal representations across a system boundary — API response, database row, external service payload; map explicitly at each of those crossings
- Between layers inside one domain, pass the same type; do not add a per-layer copy of the data — a per-layer copy turns one new field into an edit in every layer
- Write the contract first: define the function signature, return type, and error types before writing the body — callers must never depend on implementation details discovered by reading the body
- If two implementations of the same contract are conceivable, the contract is correct; if only one implementation is possible, the contract leaks implementation — generalize it

## Searchable Change Locations

A change location that text search cannot reach from the words of a request or from the message of a failure gets missed or duplicated.

- Name identifiers, files, and directories with the project's domain terms — the glossary when one exists, otherwise the words already used in the code and in the request; never introduce a synonym for a concept that already has a name (`basket` next to an existing `cart`)
- Before creating a file, find an existing file of the same kind and use its directory and its naming pattern; where no file of that kind exists yet, follow the layout rules of the applicable domain doc
- Refer to every function, class, module, route, event, and config key by its full literal name; never assemble a name from strings at runtime (`getattr(handler, "handle_" + kind)`, a computed import path) — a name that exists only at runtime cannot be found by search

## Search Before Writing

- Before writing a function, type, or constant, search for one that already does the job; if it exists, call it — do not write a second copy
- Search by the domain term and by the verb, not by a single guess — a missed search produces a duplicate that later changes update in only one place

## Change Scope

- Change only what the request names; leave code, formatting, and naming unrelated to the request as they are
- Before adding code, check whether replacing existing code achieves the request; add only when no replacement does
- After changing a function signature, a field, or shared state, search every reference to it (`reference_search` in `investigation-tools.md`) and check each one — do not stop at the first match
- Report the number of references found and the number checked; the two numbers must match

## Enforcement

A rule stated only in prose is not reliably followed, so each rule is paired with the hook that checks it. A rule with no hook is listed as unchecked to keep the gap visible. Each block is recorded in `.claude/logs/<date>_<session>/blocks/<guard>.jsonl`, one file per check, so the checks that fired in a session can be counted.

| Rule | Check |
|---|---|
| Names are literal, not assembled at runtime | `dynamic_name_guard.py` blocks the Write or Edit |
| Search every reference to a changed function | `reference_notice.py` returns the reference count and locations when a definition line changes or disappears |
| Search before writing | `reference_notice.py` returns the existing location when a new function name is already defined in another file |
| Tests before implementation | `tdd_guard.py` blocks the Write or Edit unless a staged or last-committed test file names the changed function; for a private function, a staged test must be named after the module or name the module's file. Hook code and files inside a worktree are covered. It does not check that the test failed first |
| A test asserts something; no always-true assertion, sleep, or snapshot; test names follow the convention | `testing_guard.py` blocks the Write or Edit that adds the violation (Python, JavaScript, TypeScript, Go, Rust; off while `TESTING_GUARD_DISABLE` is set) |
| Tests take every branch | `coverage_guard.py` blocks a `git commit` when a staged implementation file is below 90% coverage (off while `COVERAGE_GUARD_DISABLE` is set). Python: the lower of branch and line coverage under `pytest-cov`. TypeScript: the lower of branch and line coverage under vitest or jest. Rust: the lower of line and region coverage under `cargo llvm-cov`. Go: statement coverage under `go test`, which has no branch measure. A missing tool is installed first. Other languages are unchecked. The kit's own hooks are measured by `test_coverage.py`, every module included, and a commit that stages one runs it |
| Markdown document within 200 lines | `doc_length_guard.py` blocks the Write or Edit |
| Public functions, methods, and types carry a doc comment that fits the signature, in Google style | `doc_comment_guard.py` blocks the Write or Edit that adds the violation, including a Python docstring of more than one line without the `Args:`, `Returns:`, `Yields:`, or `Raises:` section its function needs; the doc comment linters in `static-analysis.sh` (ruff, eslint-plugin-jsdoc, revive, rustc and clippy, Checkstyle, detekt) run on each written file and at commit (Python, Go, JavaScript, TypeScript, Rust, Java, Kotlin; off while `DOC_COMMENT_GUARD_DISABLE` is set). It does not check that the comment is true |
| Domain terms as names | Unchecked — needs a project glossary |
| Same-kind files in the same place | Unchecked |
| Change only what the request names | Unchecked |
| Interfaces and mapping only at system boundaries | Unchecked |
| Dependencies are injected, not created inside a function or class | Unchecked |
| Logic is pure; one function does not mix reading, judgment, and side effects | Unchecked |
| No global state and no work at import time | Unchecked |
| A module owns one concept | Unchecked |
| A failure is returned or thrown, not swallowed; configuration is passed in | Unchecked |
| Data is validated at the entry boundary of each layer | Unchecked |
| The report gives the number of references found and the number checked | Unchecked — `reference_notice.py` returns the count; nothing reads the report |
| Function body within 20 lines | `function_length_guard.py` blocks the Write or Edit that adds a longer body or lengthens one that is already longer (Python, Go, JavaScript, TypeScript, Rust, Java, Kotlin; off while `FUNCTION_LENGTH_GUARD_DISABLE` is set) |
| A pull request or issue body has every required section of its template | `template_guard.py` blocks `gh pr create`, `gh pr edit`, `gh issue create`, and `gh issue edit` when a required section is missing or a section is empty (off while `TEMPLATE_GUARD_DISABLE` is set). It does not check that what a section says is true |
| Changed files pass static analysis | `post-edit.sh` runs `static-analysis.sh` on each project file right after it is written and hands the findings back; `static_analysis_guard.py` blocks a `git commit` when it reports a problem in a staged file (off while `STATIC_ANALYSIS_GUARD_DISABLE` is set) |
| Code file within 200 lines | The linters in `static-analysis.sh`: pylint `too-many-lines`, ESLint `max-lines` or Biome `noExcessiveLinesPerFile`, revive `file-length-limit`; for Rust and shell scripts, which have no such rule, `static-analysis.sh` counts the lines |

Limits of the checks: `reference_notice.py` matches the function name as a whole word in files git does not ignore, so an unrelated identifier with the same name is counted. Its duplicate check recognizes definitions written as `def`, `func`, `function`, `fn`, or `fun` followed by the name. `dynamic_name_guard.py` covers Python, JavaScript, TypeScript, Ruby, Java, Kotlin, and Go. Both skip test files. Each is off while its environment variable is set: `DYNAMIC_NAME_GUARD_DISABLE`, `REFERENCE_NOTICE_DISABLE`. `doc_comment_guard.py` reads Python through its syntax tree and the other languages through patterns, so it sees a definition only when its visibility is written on the definition line: a TypeScript class method with no `public` keyword and a Java interface method are not checked, a method declared in a Rust trait is not checked, and Ruby is not covered. Rust unit tests live in the source file: `testing_guard.py` reads every Rust file for them, while `tdd_guard.py` recognizes a Rust test only in a file under `tests/` or with `test` in its name. `function_length_guard.py` measures a function in those languages only when a brace opens its body right after the parameter list, so a Kotlin expression body and an arrow function passed as an argument are not measured; like `doc_comment_guard.py`, it skips test files. `tdd_guard.py` is off while `TDD_GUARD_DISABLE` is set, and lets `/update-kit` write a file whose content is identical to its copy in `.upstream/`.
