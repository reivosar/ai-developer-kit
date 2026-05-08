# Backend Rules

## API Design

- Resource-oriented URLs: `/users`, `/users/:id`, `/users/:id/posts`
- Use HTTP methods semantically: GET (read), POST (create), PUT/PATCH (update), DELETE (remove)
- Return consistent response shapes — success and error responses follow the same envelope structure
- Use ISO 8601 for all dates and times
- Field names in snake_case for JSON payloads
- Paginate all list endpoints; never return unbounded collections

## Error Handling

- Return structured errors: `{ error: { code: string, message: string } }`
- Map domain errors to appropriate HTTP status codes (400 bad input, 401 unauthenticated, 403 forbidden, 404 not found, 409 conflict, 500 unexpected)
- Never expose internal details (stack traces, SQL errors, file paths) in error responses
- Log the full error server-side; return only a safe message to the client

## Validation

- Validate all input at the boundary (controller/handler layer) before it reaches business logic
- Reject requests with unknown or extra fields to prevent mass assignment
- Validate types, ranges, lengths, and formats explicitly — never assume input is well-formed

## Security

- Authenticate before authorizing — check identity first, permissions second
- Use parameterized queries or an ORM; never concatenate user input into SQL
- Hash passwords with bcrypt or argon2; never store plaintext or use MD5/SHA1
- Enforce rate limiting on auth endpoints and public APIs
- Apply least-privilege: services and DB users have only the permissions they need

## Database

- Use transactions for operations that write to multiple tables
- Add indexes on foreign keys and columns used in WHERE/ORDER BY clauses
- Never run migrations automatically at startup in production
- Avoid N+1 queries — use joins or batch loading

## Layering

- Separate concerns: routing/controllers handle HTTP, services contain business logic, repositories handle data access
- Controllers do not contain business logic; services do not construct HTTP responses
- Keep layers thin — a handler that does more than parse input and call a service is doing too much

## Testing

- Integration tests hit the actual database; do not mock the data layer
- Unit test service logic with injected dependencies
- Test the happy path, validation errors, and auth failures for every endpoint
- Seed test data explicitly per test; do not share state between tests
