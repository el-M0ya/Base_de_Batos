"""Integration tests for the SQL exercise repository.

Covers: save, get_by_id, duplicate lookup (normalized name + muscle group),
filtered listing with ordering, translated database errors, and joint
commit/rollback across two repositories in one transaction.
"""

from __future__ import annotations

import asyncio
import unittest

from backend.tests.integration.base import IntegrationTestCase
from backend.tests.integration.support.builders import (
    build_muscle_group,
    build_trainer,
    build_user,
)
from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.infrastructure.persistence.transaction import PsqlTransactionManager
from app.infrastructure.persistence.repositories.exercise_repository_sql import (
    ExerciseRepositorySql,
)


class ExerciseRepositorySqlIntegrationTests(IntegrationTestCase):
    """Tests for :class:`ExerciseRepositorySql`."""

    async def _persist(self, tm, exercise: Exercise) -> Exercise:
        repo = self.exercise_repository(tm)
        return await repo.save(exercise)

    def test_save_and_get_by_id(self) -> None:
        trainer_user = build_user(id_user=201, name="Entrenador Repo", role="TRAINER")
        build_trainer(trainer_user, id_trainer=201)
        build_muscle_group(id_muscle_group=20, name="Piernas")

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                saved = await self._persist(
                    tm,
                    Exercise(
                        name="Sentadilla",
                        exercise_type=ExerciseType.STRENGTH,
                        intensity=IntensityLevel.HIGH,
                        muscle_group=MuscleGroup(
                            id_muscle_group=20, name="Piernas"
                        ),
                        id_trainer_creator=201,
                    ),
                )
                self.assertIsNotNone(saved.id_exercise)

                repo = self.exercise_repository(tm)
                fetched = await repo.get_by_id(saved.id_exercise)
                self.assertIsNotNone(fetched)
                self.assertEqual(fetched.name, "Sentadilla")
                self.assertEqual(fetched.id_exercise, saved.id_exercise)

        asyncio.run(scenario())

    def test_duplicate_lookup_uses_normalized_name_and_muscle_group(self) -> None:
        trainer_user = build_user(id_user=202, name="Entrenador Dup", role="TRAINER")
        build_trainer(trainer_user, id_trainer=202)
        mg_pecho = build_muscle_group(id_muscle_group=21, name="Pecho")
        build_muscle_group(id_muscle_group=22, name="Espalda")

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self.exercise_repository(tm)

                await repo.save(
                    Exercise(
                        name="Press de banca",
                        exercise_type=ExerciseType.STRENGTH,
                        intensity=IntensityLevel.HIGH,
                        muscle_group=mg_pecho,
                        id_trainer_creator=202,
                    )
                )

                # Same normalized name, same muscle group -> duplicate found.
                dup = await repo.find_duplicate("press de banca", 21)
                self.assertIsNotNone(dup)
                self.assertEqual(dup.name, "Press de banca")

                # Same normalized name, different muscle group -> NOT a duplicate.
                dup_other = await repo.find_duplicate("press de banca", 22)
                self.assertIsNone(dup_other)

                # Different name -> not a duplicate.
                dup_none = await repo.find_duplicate("remo con barra", 21)
                self.assertIsNone(dup_none)

        asyncio.run(scenario())

    def test_save_duplicate_raises_duplicate_resource(self) -> None:
        trainer_user = build_user(
            id_user=203, name="Entrenador Dup2", role="TRAINER"
        )
        build_trainer(trainer_user, id_trainer=203)
        mg_hombros = build_muscle_group(id_muscle_group=23, name="Hombros")

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self.exercise_repository(tm)

                await repo.save(
                    Exercise(
                        name="Press militar",
                        exercise_type=ExerciseType.STRENGTH,
                        intensity=IntensityLevel.HIGH,
                        muscle_group=mg_hombros,
                        id_trainer_creator=203,
                    )
                )

                with self.assertRaises(DuplicateResource):
                    await repo.save(
                        Exercise(
                            name="press militar",  # same normalized name
                            exercise_type=ExerciseType.STRENGTH,
                            intensity=IntensityLevel.HIGH,
                            muscle_group=mg_hombros,
                            id_trainer_creator=203,
                        )
                    )

        asyncio.run(scenario())

    def test_list_with_filters_and_ordering(self) -> None:
        trainer_user = build_user(
            id_user=204, name="Entrenador List", role="TRAINER"
        )
        build_trainer(trainer_user, id_trainer=204)
        build_muscle_group(id_muscle_group=24, name="Piernas")

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self.exercise_repository(tm)
                mg = MuscleGroup(id_muscle_group=24, name="Piernas")

                await repo.save(
                    Exercise(
                        name="Sentadilla",
                        exercise_type=ExerciseType.STRENGTH,
                        intensity=IntensityLevel.HIGH,
                        muscle_group=mg,
                        id_trainer_creator=204,
                    )
                )
                await repo.save(
                    Exercise(
                        name="Zancada",
                        exercise_type=ExerciseType.STRENGTH,
                        intensity=IntensityLevel.MEDIUM,
                        muscle_group=mg,
                        id_trainer_creator=204,
                    )
                )

                exercises = await repo.list(
                    muscle_group_id=24,
                    order_by="name",
                    descending=False,
                )
                self.assertEqual(len(exercises), 2)
                self.assertEqual(exercises[0].name, "Sentadilla")
                self.assertEqual(exercises[1].name, "Zancada")

                exercises_desc = await repo.list(
                    muscle_group_id=24,
                    order_by="name",
                    descending=True,
                )
                self.assertEqual(exercises_desc[0].name, "Zancada")

        asyncio.run(scenario())

    def test_get_by_id_not_found_returns_none(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self.exercise_repository(tm)
                result = await repo.get_by_id(999999)
                self.assertIsNone(result)

        asyncio.run(scenario())

    def test_invalid_order_by_raises(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self.exercise_repository(tm)
                with self.assertRaises(InvalidInput):
                    await repo.list(order_by="invalid_field")

        asyncio.run(scenario())

    def test_save_with_missing_muscle_group_raises_resource_not_found(self) -> None:
        trainer_user = build_user(id_user=205, name="Entrenador FK", role="TRAINER")
        build_trainer(trainer_user, id_trainer=205)
        build_muscle_group(id_muscle_group=25, name="Brazos")

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self.exercise_repository(tm)
                mg = MuscleGroup(id_muscle_group=99999, name="Inexistente")

                with self.assertRaises(ResourceNotFound):
                    await repo.save(
                        Exercise(
                            name="Curl de biceps",
                            exercise_type=ExerciseType.STRENGTH,
                            intensity=IntensityLevel.HIGH,
                            muscle_group=mg,
                            id_trainer_creator=205,
                        )
                    )

        asyncio.run(scenario())

    def test_joint_commit_across_two_repositories(self) -> None:
        trainer_user = build_user(
            id_user=206, name="Entrenador Joint", role="TRAINER"
        )
        build_trainer(trainer_user, id_trainer=206)
        build_muscle_group(id_muscle_group=26, name="Piernas")

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo_a = self.exercise_repository(tm)
                repo_b = self.exercise_repository(tm)

                mg = MuscleGroup(id_muscle_group=26, name="Piernas")

                await repo_a.save(
                    Exercise(
                        name="Sentadilla",
                        exercise_type=ExerciseType.STRENGTH,
                        intensity=IntensityLevel.HIGH,
                        muscle_group=mg,
                        id_trainer_creator=206,
                    )
                )
                await repo_b.save(
                    Exercise(
                        name="Zancada",
                        exercise_type=ExerciseType.STRENGTH,
                        intensity=IntensityLevel.HIGH,
                        muscle_group=mg,
                        id_trainer_creator=206,
                    )
                )

        asyncio.run(scenario())

        # Both exercises should be present because they shared one transaction.
        conn = connect_test_db(autocommit=True)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM exercise")
                self.assertEqual(cur.fetchone()[0], 2)
        finally:
            conn.close()

    def test_joint_rollback_across_two_repositories(self) -> None:
        trainer_user = build_user(
            id_user=207, name="Entrenador JointRollback", role="TRAINER"
        )
        build_trainer(trainer_user, id_trainer=207)
        build_muscle_group(id_muscle_group=27, name="Espalda")

        async def scenario() -> None:
            try:
                async with self.transaction_manager() as tm:
                    repo_a = self.exercise_repository(tm)
                    repo_b = self.exercise_repository(tm)

                    mg = MuscleGroup(id_muscle_group=27, name="Espalda")

                    await repo_a.save(
                        Exercise(
                            name="Peso muerto",
                            exercise_type=ExerciseType.STRENGTH,
                            intensity=IntensityLevel.HIGH,
                            muscle_group=mg,
                            id_trainer_creator=207,
                        )
                    )
                    await repo_b.save(
                        Exercise(
                            name="Remo con barra",
                            exercise_type=ExerciseType.STRENGTH,
                            intensity=IntensityLevel.HIGH,
                            muscle_group=mg,
                            id_trainer_creator=207,
                        )
                    )
                    raise RuntimeError("forced rollback")
            except RuntimeError:
                pass

        asyncio.run(scenario())

        conn = connect_test_db(autocommit=True)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM exercise")
                self.assertEqual(cur.fetchone()[0], 0)
        finally:
            conn.close()


def connect_test_db(autocommit: bool = True):
    from psycopg import connect as _connect

    return _connect(
        "host=localhost port=5432 dbname=basedebatos_test "
        "user=basedebatos password=basedebatos",
        autocommit=autocommit,
    )


if __name__ == "__main__":
    unittest.main()
