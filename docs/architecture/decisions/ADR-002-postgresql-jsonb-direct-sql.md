# ADR-002: PostgreSQL, JSONB, and Direct SQL

- **Status:** Accepted as the persistence baseline
- **Date:** 2026-10-26
- **Decision owners:** Project team; confirm through normal review

## Context

The application needs reliable relational data for users, clients, programs, assignments, and related records. Some routine structure is variable and benefits from JSON representation. The team prefers transparent persistence without unfamiliar ORM or migration-framework complexity.

## Decision

- Use **PostgreSQL** as the authoritative database.
- Store stable entities, relationships, identifiers, and integrity-sensitive fields in relational tables.
- Use **JSONB** for auxiliary routine_structure data where a flexible nested representation is useful; do not use JSONB instead of relational foreign keys or constraints.
- Access PostgreSQL through the project's Python PostgreSQL driver and **parameterized SQL**, without an ORM.
- Maintain schema setup and changes as ordered, versioned SQL scripts, documented and tested against a clean database.
- Validate incoming data in the application and use database constraints for suitable storage-level invariants.

## Alternatives considered

- **ORM (such as SQLAlchemy):** provides object mapping but adds concepts and configuration the team has not chosen to adopt.
- **Migration framework (such as Alembic):** useful for larger schema-evolution workflows, but not selected for this project baseline.
- **Fully relational representation:** strong integrity, but may be awkward for variable nested routine structures.
- **JSON-only storage:** flexible, but weakens relational integrity and makes relationships and queries less explicit.

## Consequences and safeguards

- SQL remains explicit and reviewable, but developers must handle row mapping and query composition carefully.
- Never concatenate untrusted values into SQL. Bind user-controlled values as parameters; allow-list dynamic identifiers that cannot be bound as values.
- Define primary keys, foreign keys, unique constraints, nullability, and indexes where appropriate.
- Validate JSONB structure at the application boundary and document its expected schema. Add database checks when suitable and maintainable.
- Translate expected database errors into stable application/API errors without exposing credentials or raw internal details.
- Keep scripts ordered, repeatable where possible, and tested on an empty database. Document prerequisites and exact execution sequence.

## Revisit when

Reconsider this decision if schema-change coordination becomes difficult, query complexity materially increases, or the team explicitly agrees to adopt an ORM/migration tool after evaluating training cost and operational benefits.
