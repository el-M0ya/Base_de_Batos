# Storage Adaptation: Relational Data and JSONB

## Storage boundary

PostgreSQL is the authoritative store. Model stable identities and relationships relationally, while using JSONB only for auxiliary routine_structure data.

| Data | Recommended representation | Reason |
|---|---|---|
| Users, roles, clients, trainers, locations | Relational tables | Stable identity, relationships, access control |
| Training programs and assignments | Relational tables | Ownership, lifecycle, dates, referential integrity |
| Exercise catalog and reusable exercise identifiers | Relational tables where shared and queried independently | Consistency and reusable references |
| Variable generated routine structure | JSONB in auxiliary routine_structure table | Nested data may vary between generated routines |
| Audit/status transitions when required | Relational records | Queryable, ordered lifecycle history |

Exact table and column names must follow the implemented repository schema. This document defines the storage principle, not an unverified schema migration.

## JSONB validation

- Validate required fields and structure in the application before persistence.
- Version the JSON structure when changes could affect existing records.
- Keep identifiers requiring referential integrity in relational columns/tables.
- Add indexes for demonstrated query patterns.
- Avoid duplicating authoritative relational values in JSONB.

## Direct SQL safety

- Use parameter placeholders supported by the selected PostgreSQL driver.
- Never build SQL by concatenating user input.
- Select dynamic table/column identifiers from a fixed allow-list.
- Use transactions for operations that must update multiple related records atomically.
- Map database exceptions to stable application errors; do not expose SQL, credentials, or stack traces in API responses.

## SQL script workflow

1. Keep schema scripts in a clearly ordered, versioned directory consistent with existing repository conventions.
2. Document prerequisites and execution order.
3. Test the full script sequence against a clean PostgreSQL database.
4. Review schema changes alongside affected repository queries and tests.
5. Do not introduce an ORM or migration framework implicitly.
