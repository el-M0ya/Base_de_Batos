"""Unit tests for the exercise use cases (E2-04).

The tests use only the standard library plus the application and domain layers:
they do not import FastAPI, psycopg or PostgreSQL. The use cases are coroutines,
so the test cases extend ``unittest.IsolatedAsyncioTestCase``.
"""

from __future__ import annotations

import dataclasses
import pathlib
import sys
import unittest
from datetime import date

# ``fakes`` is a sibling package of this test module.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from fakes.in_memory_catalog_repository import InMemoryCatalogRepository
from fakes.in_memory_exercise_repository import InMemoryExerciseRepository

from app.application.dto.actor import ActorDTO
from app.application.dto.exercise_dto import (
    CreateExerciseInputDTO,
    ListExercisesInputDTO,
)
from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.application.use_cases.create_exercise import CreateExerciseUseCase
from app.application.use_cases.list_exercise_catalogs import ListExerciseCatalogsUseCase
from app.application.use_cases.list_exercises import ListExercisesUseCase
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


CHEST = MuscleGroup(id_muscle_group=1, name="Pectoral")
BACK = MuscleGroup(id_muscle_group=2, name="Espalda")


class ExerciseUseCaseTestCase(unittest.IsolatedAsyncioTestCase):
    """Shared fixtures for the exercise use-case tests."""

    def setUp(self) -> None:
        self.catalogs = InMemoryCatalogRepository([CHEST, BACK])
        self.exercises = InMemoryExerciseRepository()
        self.create_use_case = CreateExerciseUseCase(self.exercises, self.catalogs)
        self.list_use_case = ListExercisesUseCase(self.exercises)
        self.catalogs_use_case = ListExerciseCatalogsUseCase(self.catalogs)

        self.trainer = ActorDTO(id_user=7, role="TRAINER")
        self.admin = ActorDTO(id_user=1, role="ADMIN")
        self.client = ActorDTO(id_user=42, role="CLIENT")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def create_exercise(self, **overrides: object):
        data: dict[str, object] = {
            "actor": self.trainer,
            "name": "Press de banca",
            "exercise_type": "strength",
            "intensity": "high",
            "muscle_group_id": CHEST.id_muscle_group,
        }
        data.update(overrides)
        return await self.create_use_case.execute(
            CreateExerciseInputDTO(**data)  # type: ignore[arg-type]
        )


class CreateExerciseTests(ExerciseUseCaseTestCase):
    async def test_trainer_registers_an_exercise(self) -> None:
        output = await self.create_exercise(description="  Barra y banco  ")

        self.assertEqual(output.id_exercise, 1)
        self.assertEqual(output.name, "Press de banca")
        self.assertEqual(output.description, "Barra y banco")
        self.assertEqual(output.exercise_type, "fuerza")
        self.assertEqual(output.intensity, "alto")
        self.assertEqual(output.muscle_group_id, CHEST.id_muscle_group)
        self.assertEqual(output.muscle_group_name, CHEST.name)
        self.assertEqual(output.trainer_id, self.trainer.id_user)

    async def test_registration_date_defaults_to_today(self) -> None:
        output = await self.create_exercise()

        self.assertEqual(output.registration_date, date.today())

    async def test_explicit_registration_date_is_kept(self) -> None:
        requested = date(2026, 1, 15)

        output = await self.create_exercise(registration_date=requested)

        self.assertEqual(output.registration_date, requested)

    async def test_administrator_cannot_create(self) -> None:
        with self.assertRaises(PermissionDenied):
            await self.create_exercise(actor=self.admin)

    async def test_client_cannot_create(self) -> None:
        with self.assertRaises(PermissionDenied):
            await self.create_exercise(actor=self.client)

    async def test_duplicate_with_different_case_and_accents_is_rejected(self) -> None:
        existing = await self.create_exercise(name="Sentadilla")

        with self.assertRaises(DuplicateResource) as context:
            await self.create_exercise(name="  sentádilla  ")

        error = context.exception
        self.assertEqual(error.existing.id_exercise, existing.id_exercise)
        self.assertIn(existing.name, str(error))

    async def test_same_name_in_another_muscle_group_is_allowed(self) -> None:
        first = await self.create_exercise(name="Remo")
        second = await self.create_exercise(
            name="Remo", muscle_group_id=BACK.id_muscle_group
        )

        self.assertNotEqual(first.id_exercise, second.id_exercise)
        self.assertEqual(self.exercises.count(), 2)

    async def test_unknown_muscle_group_is_rejected(self) -> None:
        with self.assertRaises(ResourceNotFound):
            await self.create_exercise(muscle_group_id=99)

    async def test_invalid_exercise_type_is_rejected(self) -> None:
        with self.assertRaises(InvalidInput):
            await self.create_exercise(exercise_type="yoga")

    async def test_invalid_intensity_is_rejected(self) -> None:
        with self.assertRaises(InvalidInput):
            await self.create_exercise(intensity="extremo")

    async def test_blank_name_is_rejected(self) -> None:
        with self.assertRaises(InvalidInput):
            await self.create_exercise(name="   ")

    def test_invalid_muscle_group_identifier_is_rejected_by_the_dto(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            CreateExerciseInputDTO(
                actor=self.trainer,
                name="Press",
                exercise_type="strength",
                intensity="high",
                muscle_group_id=0,
            )


class ListExercisesTests(ExerciseUseCaseTestCase):
    async def asyncSetUp(self) -> None:
        await self.create_exercise(
            name="Zancada", exercise_type="cardio", intensity="low"
        )
        await self.create_exercise(
            name="Abdominal", exercise_type="strength", intensity="medium"
        )
        await self.create_exercise(
            name="Remo", muscle_group_id=BACK.id_muscle_group, intensity="high"
        )

    async def test_default_ordering_is_by_name(self) -> None:
        output = await self.list_use_case.execute(
            ListExercisesInputDTO(actor=self.client)
        )

        self.assertEqual(
            [exercise.name for exercise in output], ["Abdominal", "Remo", "Zancada"]
        )

    async def test_descending_ordering(self) -> None:
        output = await self.list_use_case.execute(
            ListExercisesInputDTO(actor=self.client, descending=True)
        )

        self.assertEqual(
            [exercise.name for exercise in output], ["Zancada", "Remo", "Abdominal"]
        )

    async def test_filter_by_muscle_group(self) -> None:
        output = await self.list_use_case.execute(
            ListExercisesInputDTO(actor=self.client, muscle_group_id=BACK.id_muscle_group)
        )

        self.assertEqual([exercise.name for exercise in output], ["Remo"])

    async def test_filter_by_exercise_type(self) -> None:
        output = await self.list_use_case.execute(
            ListExercisesInputDTO(actor=self.client, exercise_type="cardio")
        )

        self.assertEqual([exercise.name for exercise in output], ["Zancada"])

    async def test_filter_by_intensity(self) -> None:
        output = await self.list_use_case.execute(
            ListExercisesInputDTO(actor=self.client, intensity="medium")
        )

        self.assertEqual([exercise.name for exercise in output], ["Abdominal"])

    async def test_every_role_can_list(self) -> None:
        for actor in (self.trainer, self.admin, self.client):
            with self.subTest(role=actor.role.value):
                output = await self.list_use_case.execute(
                    ListExercisesInputDTO(actor=actor)
                )
                self.assertEqual(len(output), 3)

    async def test_invalid_ordering_is_rejected(self) -> None:
        with self.assertRaises(InvalidInput):
            await self.list_use_case.execute(
                ListExercisesInputDTO(actor=self.client, order_by="description")
            )

    async def test_invalid_filter_value_is_rejected(self) -> None:
        with self.assertRaises(InvalidInput):
            await self.list_use_case.execute(
                ListExercisesInputDTO(actor=self.client, exercise_type="yoga")
            )


class CatalogTests(ExerciseUseCaseTestCase):
    async def test_catalogs_expose_the_three_lists(self) -> None:
        output = await self.catalogs_use_case.execute(self.trainer)

        self.assertEqual(
            [(group.id_muscle_group, group.name) for group in output.muscle_groups],
            [(BACK.id_muscle_group, "Espalda"), (CHEST.id_muscle_group, "Pectoral")],
        )
        self.assertEqual(output.exercise_types, ("fuerza", "cardio", "flexibilidad"))
        self.assertEqual(output.intensity_levels, ("bajo", "medio", "alto"))


class ImmutabilityTests(ExerciseUseCaseTestCase):
    async def test_output_dto_is_frozen(self) -> None:
        output = await self.create_exercise()

        with self.assertRaises(dataclasses.FrozenInstanceError):
            output.name = "Otro"  # type: ignore[misc]

    def test_input_dto_is_frozen(self) -> None:
        input_dto = CreateExerciseInputDTO(
            actor=self.trainer,
            name="Press",
            exercise_type="strength",
            intensity="high",
            muscle_group_id=CHEST.id_muscle_group,
        )

        with self.assertRaises(dataclasses.FrozenInstanceError):
            input_dto.name = "Otro"  # type: ignore[misc]

    async def test_listing_returns_an_immutable_sequence(self) -> None:
        await self.create_exercise()

        output = await self.list_use_case.execute(
            ListExercisesInputDTO(actor=self.client)
        )

        self.assertIsInstance(output, tuple)


class LayerIndependenceTests(unittest.TestCase):
    """The application layer must not depend on FastAPI or psycopg."""

    def test_application_sources_do_not_import_frameworks(self) -> None:
        application_dir = (
            pathlib.Path(__file__).resolve().parents[3] / "app" / "application"
        )
        forbidden = ("fastapi", "psycopg", "sqlalchemy", "pydantic")

        for source in application_dir.rglob("*.py"):
            text = source.read_text(encoding="utf-8").lower()
            for name in forbidden:
                with self.subTest(file=source.name, dependency=name):
                    self.assertNotIn(f"import {name}", text)
                    self.assertNotIn(f"from {name}", text)


if __name__ == "__main__":
    unittest.main()
