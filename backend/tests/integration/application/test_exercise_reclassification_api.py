"""Integration tests for the exercise reclassification HTTP endpoint.

These tests wire the real router, use case, error handlers and application
dependencies together, replacing only the repositories with in-memory fakes.
They verify the public ``{message, code, details}`` contract for every role and
conflict required by RF-15.
"""

from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.tests.unit.application.fakes.in_memory_catalog_repository import (
    InMemoryCatalogRepository,
)
from backend.tests.unit.application.fakes.in_memory_exercise_repository import (
    InMemoryExerciseRepository,
)
from app.adapters.dependencies import get_reclassify_exercise_use_case
from app.adapters.routers._errors import install_error_handlers
from app.adapters.routers.exercises import router as exercises_router
from app.application.use_cases.reclassify_exercise import ReclassifyExerciseUseCase
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel


CHEST = MuscleGroup(id_muscle_group=1, name="Pectoral")
BACK = MuscleGroup(id_muscle_group=2, name="Espalda")
TRAINER_ID = 7


class ExerciseReclassificationApiTests(unittest.TestCase):
    """HTTP-level tests for ``PUT /api/v1/exercises/{id}/classification``."""

    def setUp(self) -> None:
        self.catalogs = InMemoryCatalogRepository([CHEST, BACK])
        self.exercises = InMemoryExerciseRepository()
        self.use_case = ReclassifyExerciseUseCase(self.exercises, self.catalogs)
        self.exercise = self.seed_exercise()

        self.app = FastAPI()
        install_error_handlers(self.app)
        self.app.include_router(exercises_router, prefix="/api/v1")
        self.app.dependency_overrides[get_reclassify_exercise_use_case] = (
            lambda: self.use_case
        )
        self.client = TestClient(self.app)
        self.url = f"/api/v1/exercises/{self.exercise.id_exercise}/classification"

    def tearDown(self) -> None:
        self.client.close()

    def seed_exercise(
        self,
        *,
        name: str = "Press de banca",
        muscle_group: MuscleGroup = CHEST,
        creator: int = TRAINER_ID,
    ) -> Exercise:
        """Insert an exercise directly into the fake repository."""
        return self.exercises.save_sync(
            Exercise(
                name=name,
                exercise_type=ExerciseType.STRENGTH,
                intensity=IntensityLevel.HIGH,
                muscle_group=muscle_group,
                id_trainer_creator=creator,
            )
        )

    def headers(self, user_id: int = TRAINER_ID, role: str = "TRAINER") -> dict:
        return {"X-User-Id": str(user_id), "X-User-Role": role}

    def test_creator_receives_the_reclassified_exercise(self) -> None:
        response = self.client.put(
            self.url,
            headers=self.headers(),
            json={
                "exercise_type": "cardio",
                "intensity": "low",
                "muscle_group_id": BACK.id_muscle_group,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["id_exercise"], self.exercise.id_exercise)
        self.assertEqual(body["name"], self.exercise.name)
        self.assertEqual(body["exercise_type"], "cardio")
        self.assertEqual(body["intensity"], "bajo")
        self.assertEqual(body["muscle_group_id"], BACK.id_muscle_group)
        self.assertEqual(body["muscle_group_name"], BACK.name)
        self.assertEqual(body["trainer_id"], TRAINER_ID)

    def test_another_trainer_receives_permission_denied(self) -> None:
        response = self.client.put(
            self.url,
            headers=self.headers(user_id=8),
            json={
                "exercise_type": "cardio",
                "intensity": "low",
                "muscle_group_id": BACK.id_muscle_group,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "PERMISSION_DENIED")
        self.assertEqual(
            set(response.json()),
            {"message", "code", "details"},
        )

    def test_administrator_receives_permission_denied(self) -> None:
        response = self.client.put(
            self.url,
            headers=self.headers(user_id=1, role="ADMIN"),
            json={
                "exercise_type": "cardio",
                "intensity": "low",
                "muscle_group_id": BACK.id_muscle_group,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "PERMISSION_DENIED")

    def test_client_receives_permission_denied(self) -> None:
        response = self.client.put(
            self.url,
            headers=self.headers(user_id=42, role="CLIENT"),
            json={
                "exercise_type": "cardio",
                "intensity": "low",
                "muscle_group_id": BACK.id_muscle_group,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "PERMISSION_DENIED")

    def test_unknown_muscle_group_has_its_own_error_code(self) -> None:
        response = self.client.put(
            self.url,
            headers=self.headers(),
            json={
                "exercise_type": "cardio",
                "intensity": "low",
                "muscle_group_id": 99,
            },
        )

        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["code"], "MUSCLE_GROUP_NOT_FOUND")
        self.assertEqual(body["details"]["identifier"], 99)

    def test_missing_exercise_has_its_own_error_code(self) -> None:
        response = self.client.put(
            "/api/v1/exercises/999/classification",
            headers=self.headers(),
            json={
                "exercise_type": "cardio",
                "intensity": "low",
                "muscle_group_id": BACK.id_muscle_group,
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "EXERCISE_NOT_FOUND")

    def test_duplicate_conflict_has_its_own_error_code(self) -> None:
        duplicate = self.seed_exercise(
            name="  press de banca  ",
            muscle_group=BACK,
        )

        response = self.client.put(
            self.url,
            headers=self.headers(),
            json={
                "exercise_type": "cardio",
                "intensity": "low",
                "muscle_group_id": BACK.id_muscle_group,
            },
        )

        self.assertEqual(response.status_code, 409)
        body = response.json()
        self.assertEqual(body["code"], "EXERCISE_DUPLICATE")
        self.assertEqual(
            body["details"]["existing"]["id_exercise"],
            duplicate.id_exercise,
        )

    def test_invalid_catalog_value_returns_invalid_input(self) -> None:
        response = self.client.put(
            self.url,
            headers=self.headers(),
            json={
                "exercise_type": "yoga",
                "intensity": "low",
                "muscle_group_id": BACK.id_muscle_group,
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "INVALID_INPUT")

    def test_invalid_actor_role_uses_the_public_error_contract(self) -> None:
        response = self.client.put(
            self.url,
            headers={"X-User-Id": str(TRAINER_ID), "X-User-Role": "SUPERUSER"},
            json={
                "exercise_type": "cardio",
                "intensity": "low",
                "muscle_group_id": BACK.id_muscle_group,
            },
        )

        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["code"], "INVALID_INPUT")
        self.assertEqual(set(body), {"message", "code", "details"})

    def test_request_validation_uses_the_public_error_contract(self) -> None:
        response = self.client.put(
            self.url,
            headers=self.headers(),
            json={
                "exercise_type": "cardio",
                "muscle_group_id": BACK.id_muscle_group,
            },
        )

        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["code"], "VALIDATION_ERROR")
        self.assertEqual(set(body), {"message", "code", "details"})
        self.assertTrue(body["details"])


if __name__ == "__main__":
    unittest.main()
