# Frontend Rules

## Components

- One component per file; filename matches the component name in PascalCase
- Keep components small and focused — if a component needs more than one screen of code, split it
- Co-locate styles, tests, and sub-components with the component they belong to
- Prefer composition over prop drilling; lift state only as high as necessary

## Naming

- Components: PascalCase (`UserCard`, `LoginForm`)
- Hooks: camelCase prefixed with `use` (`useAuth`, `usePagination`)
- Event handlers: prefixed with `handle` (`handleSubmit`, `handleClick`)
- Boolean props/variables: prefixed with `is`, `has`, or `can` (`isLoading`, `hasError`)

## State Management

- Local UI state: component-level state (`useState`)
- Shared UI state: context or lightweight global store
- Server state: dedicated data-fetching library (React Query, SWR, etc.) — do not manually manage loading/error/data in local state
- Avoid storing derived data in state; compute it from existing state instead

## TypeScript

- Strict mode enabled
- No `any` — use `unknown` and narrow explicitly if the type is truly unknown
- Prefer `interface` for object shapes, `type` for unions and primitives
- Export prop types alongside their components

## Styling

- Use CSS variables for colors, spacing, and typography tokens
- Avoid inline styles except for dynamic values that cannot be expressed in CSS
- Responsive design mobile-first; use breakpoints consistently

## Accessibility

- Use semantic HTML elements (`button`, `nav`, `main`, `section`) over generic `div`
- Every interactive element must be keyboard-accessible and have a visible focus state
- Images require `alt` text; decorative images use `alt=""`
- Form inputs must have associated `label` elements

## Error & Loading States

- Every async operation must handle loading, error, and empty states explicitly
- Show meaningful error messages to the user — never silently swallow errors
- Use skeleton screens or spinners consistently; do not mix both in the same product

## Testing

- Test behavior, not implementation — assert what the user sees and can do
- Unit test pure functions and custom hooks in isolation
- Component tests cover the main interaction flow and key edge cases
- Avoid snapshot tests; they break on trivial changes and provide little signal
