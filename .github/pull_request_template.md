## Goal

Build the persistence foundation for the remaining repositories using direct, parameterized SQL and psycopg. Provide transaction management, a safe integration-test database, and the first concrete repository.

Closes #89

## Changes Made

- Add `TransactionManager` port (`backend/app/application/ports/transaction_manager.py`) and psycopg implementation (`backend/app/infrastructure/persistence/transaction.py`): commits on success, rolls back on exceptions, per-request scoped connection shared across repositories.
- Add `ExerciseRepositorySql` (`backend/app/infrastructure/persistence/repositories/exercise_repository_sql.py`): parameterized queries, `user` quoted as reserved identifier, duplicate detection by normalized name + muscle group (U-12), translated database errors (UniqueViolation → DuplicateResource, ForeignKeyViolation → ResourceNotFound, CheckViolation → InvalidInput), no psycopg messages leaked to callers.
- Add integration test database support (`backend/tests/integration/support/database.py`): creates `basedebatos_test`, applies scripts 001–008 in order from Python without `psql`, blocks destructive cleanup unless the database name ends in `_test`.
- Add test-data builders (`backend/tests/integration/support/builders.py`): site, muscle_group, user, trainer, client, workout_program, exercise — respecting the E1-08 role/specialization trigger (user inserted first with correct role, then trainer/client).
- Add `IntegrationTestCase` base (`backend/tests/integration/base.py`): setUp/tearDown with clean database per test.
- Add integration tests:
  - `test_transaction_manager.py`: commit on success, rollback on exception, shared connection across two repositories in one transaction, joint rollback.
  - `test_exercise_repository.py`: save/get_by_id, duplicate lookup (same group vs different group), filtered listing with ordering, 404 on missing id, invalid order_by, missing muscle group → ResourceNotFound, joint commit and rollback across two repositories.
- Add `.github/pull_request_template.md`.
- Add test DB variables to `.env.example` (`TEST_POSTGRES_*`).

Acceptance criteria covered:
- [x] Transaction manager commits on success and rolls back on exceptions.
- [x] Repositories participating in one operation share the same request-scoped connection/transaction.
- [x] Test database scripts run in order from Python without requiring `psql`.
- [x] Destructive test cleanup is blocked unless the database name ends in `_test`.
- [x] Builders respect the E1-08 role/specialization trigger.
- [x] Exercise repository supports save, get by id, duplicate lookup, filtered listing, and ordering.
- [x] U-12 duplicate behavior matches the domain normalization rule and the actual script `006` index.
- [x] Database errors are translated to application errors without leaking driver messages.
- [x] Integration tests cover creation, lookup, duplicate in the same group, same name in different groups, filters, translated errors, and joint commit/rollback across two repositories.
- [x] Changes are reviewed through a pull request before merging.

## Checklist

- [ ] Tests pass locally
- [ ] Database scripts applied in order without `psql`
- [ ] No psycopg errors leak to the HTTP client
- [ ] Pull request reviewed before merging
