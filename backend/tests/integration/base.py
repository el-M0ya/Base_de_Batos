"""Base class for the integration tests that need PostgreSQL.

``setUpClass`` creates the dedicated ``<POSTGRES_DB>_test`` database and applies
``backend/database/scripts/*.sql`` in order (once per process). ``asyncSetUp``
opens an async pool against the test database, builds a transaction manager and
an exercise repository that share the request-scoped connection, and empties the
tables so each test starts from a known state.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from support.database import (  # noqa: E402
    apply_scripts,
    conninfo_for,
    database_available,
    recreate_test_database,
    test_database_name,
    truncate_all,
)

from app.infrastructure.persistence.repositories.exercise_repository_sql import (  # noqa: E402
    PostgresExerciseRepository,
)
from app.infrastructure.persistence.transaction import PostgresTransactionManager  # noqa: E402

_PREPARED_DATABASES: set[str] = set()


class IntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    """Common fixture: test database, pool, transaction manager and repository."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if not database_available():
            raise unittest.SkipTest(
                "PostgreSQL is not available. Start it with "
                "`docker compose up -d --wait` (or your local service) and set "
                "POSTGRES_* in the environment or backend/.env."
            )
        name = test_database_name()
        if name not in _PREPARED_DATABASES:
            recreate_test_database(name)
            apply_scripts(name)
            _PREPARED_DATABASES.add(name)

    async def asyncSetUp(self) -> None:
        self.pool = AsyncConnectionPool(
            conninfo=conninfo_for(test_database_name()),
            min_size=1,
            max_size=2,
            open=False,
            kwargs={"row_factory": dict_row},
            name="e2-06-test-pool",
        )
        await self.pool.open(wait=True)

        self.manager = PostgresTransactionManager(self.pool)
        self.exercises = PostgresExerciseRepository(lambda: self.manager.connection)

        async with self.pool.connection() as connection:
            await truncate_all(connection)

    async def asyncTearDown(self) -> None:
        await self.pool.close()
