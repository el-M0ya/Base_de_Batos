# ADR-001: Adopt Clean Architecture

- **Status:** Accepted as the project architecture baseline
- **Date:** 2026-10-26
- **Decision owners:** Project team; confirm through normal review

## Context

The system has business rules for generating, reviewing, adjusting, approving, and assigning training programs. These rules should remain testable and independent from HTTP handling, React UI code, and PostgreSQL implementation details.

## Decision

Organize the backend into Domain, Application, Interface Adapters, and Infrastructure layers. Source dependencies point inward. Domain contains business concepts and invariants; Application contains use cases and contracts; interface adapters translate HTTP/API data; infrastructure provides concrete database access and dependency wiring. React + TypeScript communicates with FastAPI only through API contracts.

## Alternatives considered

- **Layered architecture without explicit dependency inversion:** simpler initially, but business rules can become dependent on database or framework details.
- **Framework-centric design:** convenient for a prototype, but increases coupling and makes isolated testing harder.
- **Microservices:** adds deployment and communication overhead not justified by the current scope.

## Consequences

- Use cases can be tested independently from FastAPI and PostgreSQL.
- Repository contracts belong inward; SQL-backed implementations belong in Infrastructure.
- API request/response models are mapped at adapter boundaries.
- Code review must preserve dependency direction.
- The structure adds interfaces, so implementations should remain proportionate to project size.

## Validation

Review imports and module boundaries, test domain rules without infrastructure, and verify that frontend code accesses the backend only through the API.
