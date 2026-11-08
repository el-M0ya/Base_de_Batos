"""Integration tests for ``PostgresTransactionManager`` (E2-06).

They need a real PostgreSQL instance and are skipped when it is unavailable.
"""

from __future__ import annotations

import pathlib
import sys

import psycopg

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from base import IntegrationTestCase  # noqa: E402
from support.builders import create_muscle_group, create_site, create_trainer  # noqa: E402
from support.database import conninfo_for, test_database_name  # noqa: E402

from app.domain.entities.exercise import Exercise  # noqa: E402
from app.domain.entities.muscle_group import MuscleGroup  # noqa: E402
from app.domain.value_objects.exercise_type import ExerciseType  # noqa: E402
from app.domain.value_objects.intensity_level import IntensityLevel  # noqa: E402


class TransactionManagerTests(IntegrationTestCase):
    async def count_rows(self, table: str) -> int:
        """Count rows of a table using a connection outside the manager."""
        async with await psycopg.AsyncConnection.connect(
            conninfo_for(test_database_name())
        ) as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(f"SELECT COUNT(*) AS total FROM {table}")
                return (await cursor.fetchone())[0]

    async def seed_catalog_and_trainer(self) -> tuple[int, MuscleGroup]:
        async with self.manager.transaction():
            async with self.manager.connection.cursor() as cursor:
                trainer_id = await create_trainer(cursor)
                group_id = await create_muscle_group(cursor, "Pectoral")
            return trainer_id, MuscleGroup(id_muscle_group=group_id, name="Pectoral")

    async def test_commit_persists_the_changes(self) -> None:
        async with self.manager.transaction():
            async with self.manager.connection.cursor() as cursor:
                await create_site(cursor, "Sede comprometida")

        self.assertEqual(await self.count_rows("site"), 1)

    async def test_exception_rolls_everything_back(self) -> None:
        with self.assertRaises(RuntimeError):
            async with self.manager.transaction():
                async with self.manager.connection.cursor() as cursor:
                    await create_site(cursor, "Sede revertida")
                raise RuntimeError("fallo a mitad de la operación")

        self.assertEqual(await self.count_rows("site"), 0)

    async def test_nested_transaction_joins_the_outer_one(self) -> None:
        async with self.manager.transaction():
            connection = self.manager.connection
            async with self.manager.connection.cursor() as cursor:
                await create_site(cursor, "Sede externa")

            async with self.manager.transaction():
                self.assertIs(self.manager.connection, connection)
                async with self.manager.connection.cursor() as cursor:
                    await create_site(cursor, "Sede anidada")

        self.assertEqual(await self.count_rows("site"), 2)

    async def test_outer_rollback_discards_the_nested_work(self) -> None:
        with self.assertRaises(RuntimeError):
            async with self.manager.transaction():
                async with self.manager.transaction():
                    async with self.manager.connection.cursor() as cursor:
                        await create_site(cursor, "Sede anidada")
                raise RuntimeError("fallo después del bloque anidado")

        self.assertEqual(await self.count_rows("site"), 0)

    async def test_two_repositories_share_the_transaction(self) -> None:
        trainer_id, muscle_group = await self.seed_catalog_and_trainer()
        first = self.exercises
        second = type(self.exercises)(lambda: self.manager.connection)

        with self.assertRaises(RuntimeError):
            async with self.manager.transaction():
                await first.save(
                    Exercise(
                        name="Press de banca",
                        exercise_type=ExerciseType.STRENGTH,
                        intensity=IntensityLevel.HIGH,
                        muscle_group=muscle_group,
                        id_trainer_creator=trainer_id,
                    )
                )
                await second.save(
                    Exercise(
                        name="Remo con barra",
                        exercise_type=ExerciseType.STRENGTH,
                        intensity=IntensityLevel.MEDIUM,
                        muscle_group=muscle_group,
                        id_trainer_creator=trainer_id,
                    )
                )
                raise RuntimeError("cancelamos la operación completa")

        self.assertEqual(await self.count_rows("exercise"), 0)
