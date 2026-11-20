"""Base class for integration tests against a real PostgreSQL database.

Creates the dedicated test database (``basedebatos_test``) once per class,
applies every schema script in order, and truncates all tables before each test
so they run in isolation.

The database name ends in ``_test`` so destructive cleanup is allowed.
"""

from __future__ import annotations

import asyncio
import unittest

from backend.tests.integration.support.database import (
    apply_schema_scripts,
    clean_all_tables,
    close_test_pool,
    create_test_database,
    drop_test_database,
    get_test_pool,
)
from backend.tests.integration.support.builders import (
    build_client,
    build_exercise,
    build_muscle_group,
    build_site,
    build_trainer,
    build_user,
    build_workout_program,
)
from app.application.ports.transaction_manager import TransactionManager
from app.infrastructure.persistence.transaction import PsqlTransactionManager
from app.infrastructure.persistence.repositories.exercise_repository_sql import (
    ExerciseRepositorySql,
)


class IntegrationTestCase(unittest.TestCase):
    """Base class for integration tests."""

    @classmethod
    def setUpClass(cls) -> None:
        asyncio.run(cls._async_set_up_class())

    @classmethod
    async def _async_set_up_class(cls) -> None:
        await create_test_database()
        await apply_schema_scripts()
        await get_test_pool()

    @classmethod
    def tearDownClass(cls) -> None:
        asyncio.run(cls._async_tear_down_class())

    @classmethod
    async def _async_tear_down_class(cls) -> None:
        await close_test_pool()
        await drop_test_database()

    def setUp(self) -> None:
        asyncio.run(clean_all_tables())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def transaction_manager(self) -> TransactionManager:
        """Return a new :class:`PsqlTransactionManager` bound to the test pool."""
        return PsqlTransactionManager()

    def exercise_repository(
        self, transaction_manager: TransactionManager
    ) -> ExerciseRepositorySql:
        """Return an ``ExerciseRepositorySql`` using the given transaction manager."""
        return ExerciseRepositorySql(transaction_manager)
