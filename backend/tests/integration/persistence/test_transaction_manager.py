"""Integration tests for the transaction manager.

Verifies that commits happen on success, rollbacks on exceptions, and that
multiple repositories share the same request-scoped connection inside one
transaction block.
"""

from __future__ import annotations

import asyncio
import unittest

from psycopg import connect

from backend.tests.integration.base import IntegrationTestCase
from backend.tests.integration.support.builders import (
    build_muscle_group,
    build_trainer,
    build_user,
)
from backend.tests.integration.support.database import _target_db_dsn
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.infrastructure.persistence.transaction import PsqlTransactionManager
from app.infrastructure.persistence.repositories.exercise_repository_sql import (
    ExerciseRepositorySql,
)


def _count_exercises() -> int:
    conn = connect(_target_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM exercise")
            return cur.fetchone()[0]
    finally:
        conn.close()


def _make_exercise(
    name: str,
    muscle_group: MuscleGroup,
    id_trainer_creator: int,
    intensity: str = "alto",
) -> Exercise:
    return Exercise(
        name=name,
        exercise_type=ExerciseType.STRENGTH,
        intensity=IntensityLevel.from_value(intensity),
        muscle_group=muscle_group,
        id_trainer_creator=id_trainer_creator,
    )


class TransactionManagerIntegrationTests(IntegrationTestCase):
    """Tests for :class:`PsqlTransactionManager`."""

    def test_commits_on_success(self) -> None:
        trainer_user = build_user(id_user=101, name="Entrenador Commit", role="TRAINER")
        build_trainer(trainer_user, id_trainer=101)
        build_muscle_group(id_muscle_group=10, name="Piernas")

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self.exercise_repository(tm)
                saved = await repo.save(
                    _make_exercise(
                        "Sentadilla",
                        MuscleGroup(id_muscle_group=10, name="Piernas"),
                        101,
                    )
                )
                self.assertIsNotNone(saved.id_exercise)

        asyncio.run(scenario())

        self.assertEqual(_count_exercises(), 1)

    def test_rolls_back_on_exception(self) -> None:
        trainer_user = build_user(
            id_user=102, name="Entrenador Rollback", role="TRAINER"
        )
        build_trainer(trainer_user, id_trainer=102)
        build_muscle_group(id_muscle_group=11, name="Espalda")

        async def scenario() -> None:
            try:
                async with self.transaction_manager() as tm:
                    repo = self.exercise_repository(tm)
                    await repo.save(
                        _make_exercise(
                            "Peso muerto",
                            MuscleGroup(id_muscle_group=11, name="Espalda"),
                            102,
                        )
                    )
                    raise RuntimeError("forced rollback")
            except RuntimeError:
                pass

        asyncio.run(scenario())

        self.assertEqual(_count_exercises(), 0)

    def test_repositories_share_the_same_connection_and_transaction(self) -> None:
        trainer_user = build_user(
            id_user=103, name="Entrenador Compartido", role="TRAINER"
        )
        build_trainer(trainer_user, id_trainer=103)
        build_muscle_group(id_muscle_group=12, name="Pecho")

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo_a = self.exercise_repository(tm)
                repo_b = self.exercise_repository(tm)

                # Both repositories must use the same underlying connection.
                self.assertIs(repo_a._conn, repo_b._conn)

                saved_a = await repo_a.save(
                    _make_exercise(
                        "Press de banca",
                        MuscleGroup(id_muscle_group=12, name="Pecho"),
                        103,
                    )
                )
                saved_b = await repo_b.save(
                    _make_exercise(
                        "Press militar",
                        MuscleGroup(id_muscle_group=12, name="Pecho"),
                        103,
                    )
                )

                self.assertIsNotNone(saved_a.id_exercise)
                self.assertIsNotNone(saved_b.id_exercise)

        asyncio.run(scenario())

        self.assertEqual(_count_exercises(), 2)

    def test_rollback_undoes_all_repositories_in_the_same_block(self) -> None:
        trainer_user = build_user(
            id_user=104, name="Entrenador Atomic", role="TRAINER"
        )
        build_trainer(trainer_user, id_trainer=104)
        build_muscle_group(id_muscle_group=13, name="Hombros")

        async def scenario() -> None:
            try:
                async with self.transaction_manager() as tm:
                    repo = self.exercise_repository(tm)
                    await repo.save(
                        _make_exercise(
                            "Press militar",
                            MuscleGroup(id_muscle_group=13, name="Hombros"),
                            104,
                        )
                    )
                    raise RuntimeError("forced rollback")
            except RuntimeError:
                pass

        asyncio.run(scenario())

        self.assertEqual(_count_exercises(), 0)


if __name__ == "__main__":
    unittest.main()
