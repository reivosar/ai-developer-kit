# Frontend Design Rules

## Component Responsibility

- A component does one thing: either renders UI or manages logic, not both
- Container components fetch data and manage state; presentational components receive props and render
- If a component has more than one reason to change, split it
- Reusable components must not depend on application-specific context (routing, auth, global store)

## Component Boundaries

- Split when: a piece of UI is reused in multiple places, a section has independent loading/error state, or a component exceeds one screen
- Do not split prematurely — duplication is acceptable until the pattern is clear
- Group components by feature, not by type; keep related components together

## State Design

- State lives as close to where it is used as possible
- Lift state only when two components genuinely need to share it
- Do not put server data into local state — use a data-fetching layer (React Query, SWR, etc.)
- Derived values are computed, not stored; storing derived state causes sync bugs

## Data Flow

- Data flows down through props; events flow up through callbacks
- Avoid cross-cutting state that bypasses the component tree — use context only for truly global concerns (theme, auth, locale)
- Side effects belong in hooks or dedicated effect layers, not in render logic

## Page / Feature Structure

- A page composes features; a feature composes components
- Business logic belongs in hooks or service modules, not in JSX
- Keep pages thin — a page component's job is layout and composition, not logic

## Error & Loading Design

- Every async boundary must account for three states: loading, error, and success
- Error states must be recoverable where possible (retry, redirect, fallback)
- Empty states are a distinct state — design them explicitly, do not treat them as a loading edge case
