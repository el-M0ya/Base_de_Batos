"""Integration tests for ``PostgresExerciseRepository`` (E2-06).

They need a real PostgreSQL instance and are skipped when it is unavailable.
"""

from __future__ import annotations

import pathlib
import sys

import psycopg

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from base import IntegrationTestCase  # noqa: E402
from support.builders import create_muscle_group, create_trainer  # noqa: E402

from app.application.exceptions import DuplicateResource, InvalidInput, ResourceNotFound  # noqa: E402
from app.domain.entities.exercise import Exercise  # noqa: E402
from app.domain.entities.muscle_group import MuscleGroup  # noqa: E402
from app.domain.value_objects.exercise_type import ExerciseType  # noqa: E402
from app.domain.value_objects.intensity_level import IntensityLevel  # noqa: E402
from app.infrastructure.persistence.repositories.exercise_repository_sql import (  # noqa: E402
    translate_database_error,
)


class ExerciseRepositoryTests(IntegrationTestCase):
    async def seed(self) -> dict:
        """Create a trainer and two muscle groups, committed before the test."""
        async with self.manager.transaction():
            async with self.manager.connection.cursor() as cursor:
                trainer_id = await create_trainer(cursor)
                chest_id = await create_muscle_group(cursor, "Pectoral")
                back_id = await create_muscle_group(cursor, "Espalda")
        return {
            "trainer": trainer_id,
            "chest": MuscleGroup(id_muscle_group=chest_id, name="Pectoral"),
            "back": MuscleGroup(id_muscle_group=back_id, name="Espalda"),
        }

    def build(self, muscle_group: MuscleGroup, trainer_id: int, **overrides) -> Exercise:
        data = {
            "name": "Press de banca",
            "exercise_type": ExerciseType.STRENGTH,
            "intensity": IntensityLevel.HIGH,
            "muscle_group": muscle_group,
            "id_trainer_creator": trainer_id,
            "description": "Barra y banco",
        }
        data.update(overrides)
        return Exercise(**data)

    async def test_save_and_get_by_id_roundtrip(self) -> None:
        ids = await self.seed()

        async with self.manager.transaction():
            saved = await self.exercises.save(
                self.build(ids["chest"], ids["trainer"])
            )

        self.assertIsNotNone(saved.id_exercise)
        async with self.manager.transaction():
            loaded = await self.exercises.get_by_id(saved.id_exercise)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Press de banca")
        self.assertEqual(loaded.exercise_type, ExerciseType.STRENGTH)
        self.assertEqual(loaded.intensity, IntensityLevel.HIGH)
        self.assertEqual(loaded.muscle_group.name, "Pectoral")
        self.assertEqual(loaded.id_trainer_creator, ids["trainer"])
        self.assertEqual(loaded.description, "Barra y banco")

    async def test_duplicate_in_the_same_group_is_translated(self) -> None:
        ids = await self.seed()
        async with self.manager.transaction():
            await self.exercises.save(self.build(ids["chest"], ids["trainer"]))

        with self.assertRaises(DuplicateResource):
            async with self.manager.transaction():
                await self.exercises.save(
                    self.build(
                        ids["chest"],
                        ids["trainer"],
                        name="  PRÉSS   DE BANCA ",
                    )
                )

    async def test_find_duplicate_uses_the_normalized_name(self) -> None:
        ids = await self.seed()
        async with self.manager.transaction():
            saved = await self.exercises.save(
                self.build(ids["chest"], ids["trainer"], name="Sentadilla")
            )

        async with self.manager.transaction():
            duplicate = await self.exercises.find_duplicate(
                "sentádilla", ids["chest"].id_muscle_group
            )

        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate.id_exercise, saved.id_exercise)

    async def test_same_name_in_another_group_is_allowed(self) -> None:
        ids = await self.seed()
        async with self.manager.transaction():
            first = await self.exercises.save(self.build(ids["chest"], ids["trainer"]))
            second = await self.exercises.save(self.build(ids["back"], ids["trainer"]))

        self.assertNotEqual(first.id_exercise, second.id_exercise)

    async def test_list_filters_and_orders(self) -> None:
        ids = await self.seed()
        async with self.manager.transaction():
            await self.exercises.save(
                self.build(ids["chest"], ids["trainer"], name="Zancada",
                           exercise_type=ExerciseType.CARDIO,
                           intensity=IntensityLevel.LOW)
            )
            await self.exercises.save(
                self.build(ids["back"], ids["trainer"], name="Remo",
                           intensity=IntensityLevel.MEDIUM)
            )

        async with self.manager.transaction():
            every = await self.exercises.list()
            chest = await self.exercises.list(muscle_group_id=ids["chest"].id_muscle_group)
            cardio = await self.exercises.list(exercise_type=ExerciseType.CARDIO)
            medium = await self.exercises.list(intensity=IntensityLevel.MEDIUM)
            descending = await self.exercises.list(descending=True)

        self.assertEqual([exercise.name for exercise in every], ["Remo", "Zancada"])
        self.assertEqual([exercise.name for exercise in chest], ["Zancada"])
        self.assertEqual([exercise.name for exercise in cardio], ["Zancada"])
        self.assertEqual([exercise.name for exercise in medium], ["Remo"])
        self.assertEqual([exercise.name for exercise in descending], ["Zancada", "Remo"])

    async def test_missing_trainer_is_translated_to_not_found(self) -> None:
        ids = await self.seed()

        with self.assertRaises(ResourceNotFound):
            async with self.manager.transaction():
                await self.exercises.save(
                    self.build(ids["chest"], trainer_id=999_999)
                )

    def test_check_violation_is_translated_without_leaking_the_driver(self) -> None:
        error = psycopg.errors.CheckViolation("mensaje interno del driver")
        error.diag.constraint_name = "chk_exercise_name_not_empty"

        translated = translate_database_error(error)

        self.assertIsInstance(translated, InvalidInput)
        self.assertNotIn("driver", str(translated))
        self.assertIn("chk_exercise_name_not_empty", str(translated))
