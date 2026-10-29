# Architecture Overview

## Purpose and stack

The application generates and manages training programs. The agreed stack is a React + TypeScript frontend, a FastAPI backend, and PostgreSQL persistence. The backend follows Clean Architecture to keep business rules independent from delivery and storage technologies.

## Layers and responsibilities

1. **Domain** — business entities, value objects, domain rules, and domain services. It must not depend on FastAPI, React, PostgreSQL drivers, or infrastructure.
2. **Application** — use cases that coordinate domain behavior, define input/output models, and depend on repository/service contracts rather than concrete adapters.
3. **Interface adapters** — API controllers/routes, request and response mapping, and translation between external formats and application models.
4. **Infrastructure** — concrete PostgreSQL access, parameterized SQL, external integrations, configuration, and dependency wiring.

Dependencies point inward: outer layers may depend on inner-layer abstractions; Domain does not import infrastructure. Dependency injection at the composition boundary provides concrete repository implementations to use cases.

## Request flow

React sends an HTTP request to FastAPI. A route/controller validates transport-level data and invokes an application use case. The use case applies domain rules and uses repository contracts. Infrastructure adapters execute parameterized SQL against PostgreSQL and return data. The controller maps the result to an HTTP response.

## Persistence

PostgreSQL is the system of record. Relational tables hold structured entities and relationships; JSONB is reserved for auxiliary routine_structure data whose shape can vary. SQL statements must be parameterized. Schema setup and changes use versioned SQL scripts; the project does not introduce an ORM or migration framework.

## Frontend boundary

The React frontend communicates through the backend API and must not access PostgreSQL directly or import backend domain classes. API schemas are the integration contract. UI concerns remain in the frontend; business invariants remain in backend Domain/Application layers.

## Testing boundaries

- Domain: unit tests for business rules without database or web-framework dependencies.
- Application: use-case tests with repository contracts stubbed or faked.
- Adapters/infrastructure: integration tests for HTTP mapping and PostgreSQL queries where practical.
- Frontend: tests for user interactions and API-contract handling.

## Non-goals

This architecture does not require SQLAlchemy, Alembic, Redis, or another persistence/migration service. Add infrastructure dependencies only after an explicit team decision and documented rationale.
