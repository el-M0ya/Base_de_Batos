# Integration tests

These tests exercise the real adapters against PostgreSQL. They are skipped, not
failed, when the database is unavailable, so the unit-test workflow keeps
working on machines without PostgreSQL.

## How the test database is built

- The target database is `<POSTGRES_DB>_test` (for example `basedebatos_test`).
  It is **never** the development database.
- `tests/integration/support/database.py` drops and recreates it, then applies
  every file of `backend/database/scripts/*.sql` in file-name order, directly
  from Python. The `psql` executable is not required.
- Every destructive helper (`recreate_test_database`, `apply_scripts`,
  `truncate_all`) refuses to run unless the database name ends with `_test`
  (`UnsafeTestDatabase`).
- `IntegrationTestCase` truncates every public table between tests, so each test
  starts from an empty schema and builds only the data it needs.

## Running them

```powershell
cd backend
python -m pytest tests/integration -q
```

or, with the standard library runner:

```powershell
python -m unittest discover -s tests/integration -t tests/integration
```

PostgreSQL must be reachable with the `POSTGRES_*` values of `backend/.env`
(or the environment). With the compose file:

```powershell
docker compose up -d --wait
```

## Writing a test

```python
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from base import IntegrationTestCase
from support.builders import create_muscle_group, create_trainer


class MyRepositoryTests(IntegrationTestCase):
    async def test_something(self) -> None:
        async with self.manager.transaction():
            async with self.manager.connection.cursor() as cursor:
                trainer_id = await create_trainer(cursor)
                group_id = await create_muscle_group(cursor, "Pectoral")
```

`self.manager` is a `PostgresTransactionManager` and `self.exercises` is a
`PostgresExerciseRepository` wired to the same per-request connection.

## Builders

`support/builders.py` inserts valid rows for sites, muscle groups, exercise
types, intensity levels, users, trainers, clients, workout programs and
exercises. `create_trainer` and `create_client` insert the `app_user` row and
its specialization in the same transaction and in the order the E1-08 triggers
(`trg_check_trainer_user_role`, `trg_check_client_user_role`) accept: user first,
specialization second.
