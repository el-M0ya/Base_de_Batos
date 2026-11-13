# Integration tests

This directory contains integration tests that run against a real PostgreSQL
database. They are **not** unit tests: they require a running PostgreSQL
instance (see ``compose.yaml``) and are skipped when the database is unavailable.

## Test database

A dedicated database called ``basedebatos_test`` is created automatically. The
name ends in ``_test`` so destructive cleanup is allowed.

All schema scripts from ``backend/database/scripts/`` are applied in order
(001 through 008) before the test suite runs. Every table is truncated between
tests so each test starts from a clean slate.

## How to run

From the repository root:

```bash
# Start PostgreSQL (and Redis)
docker compose up -d --wait

# Run the integration test suite from backend/
cd backend
python -m unittest discover -s tests/integration -p 'test_*.py' -v
```

Tests are skipped (not failed) when PostgreSQL is not available.
