# Backend Design Rules

## Business Logic Belongs in the Service Layer

- Controllers/handlers handle only HTTP concerns: parse input, call a service, format the response
- Business rules (calculations, workflows, eligibility, state transitions) live in the service/domain layer
- A controller that contains an `if` checking a business condition is doing too much
- The service layer must be callable without HTTP — it knows nothing about request/response objects

## Dependency Direction

- Outer layers depend on inner layers; inner layers never depend on outer layers
- Direction: handler → service → repository → database; never the reverse
- The service layer does not import from the HTTP framework, the database driver, or external SDKs directly
- Infrastructure (DB, email, storage, queues) adapts to the domain through interfaces — the domain does not adapt to infrastructure

## Data Transformation at the Boundary

- Raw input (HTTP request, message body) is validated and mapped to domain objects at the entry boundary
- Internal domain models never leak into API responses — map to response DTOs at the exit boundary
- If the DB schema changes, only the repository layer changes; services are unaffected
- If the API contract changes, only the controller layer changes; services are unaffected

## Layering Responsibilities

- **Handler/Controller**: authenticate, validate input shape, call one service method, map result to response
- **Service/Use Case**: business logic, orchestration of repositories and external adapters, transaction boundary
- **Repository**: data access only — no business logic, no HTTP concerns
- **Domain Model**: entities and value objects expressing business concepts — no framework dependencies

## Transaction Boundaries

- A single service method represents a single unit of work — it either fully succeeds or fully rolls back
- Transactions are managed at the service layer, not in the repository or controller
- Never spread a transaction across multiple service calls — caller cannot know what to roll back

## External Dependencies Through Interfaces

- External services (email, payment, storage, push notifications) are accessed through interfaces defined by the domain
- The service layer depends on the interface; the concrete implementation is injected
- This keeps business logic testable and allows swapping implementations without touching service code
- Never call an external service SDK directly from a service — wrap it in an adapter

## Authentication and Authorization

- Authentication (who is this?) is handled at the middleware layer before the handler is reached
- Authorization (can they do this?) is checked at the start of the service method, before any business logic runs
- Services assume the caller is authenticated — they do not re-verify identity
- Permission checks are explicit and close to the operation they protect, not buried in business logic

## API Contract Design

- APIs are designed for consumers, not for internal convenience
- Request and response shapes are stable contracts — internal refactoring must not change them
- Breaking changes require versioning; additive changes (new optional fields) are non-breaking
- Internal domain concepts (table names, internal IDs, implementation details) do not appear in the API

## Error Design

- Domain errors are first-class: define specific error types for each failure mode (NotFound, Conflict, Unauthorized)
- The controller maps domain errors to HTTP status codes — the service does not know about HTTP
- Infrastructure errors (DB failure, network timeout) are caught, logged in full, and wrapped into safe domain errors before propagating
- Never let a raw database error or stack trace reach the API response

## State Transitions

- Mutating operations must validate that the current state permits the transition before executing
- Illegal state transitions are rejected with a domain error, not silently ignored or partially applied
- Side effects (emails, events, notifications) triggered by a state change happen after the transaction commits, not inside it
