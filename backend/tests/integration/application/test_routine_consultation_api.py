"""Integration tests for the routine consultation HTTP API (RF-19).

Uses FastAPI's TestClient with overridden dependencies so no live database is
required. Covers trainers in the same program, different programs, empty
results, and unauthorized access.
"""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.adapters.dependencies import get_current_actor
from app.application.dto.actor import ActorDTO
from app.application.dto.routine_dto import (
    ListRoutinesForTrainerInputDTO,
    RoutineSummaryDTO,
)
from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.repositories.routine_consultation_repository import (
    RoutineConsultationRepository,
)
from app.domain.value_objects.user_role import UserRole
from app.main import app


class _FakeConsultationRepository(RoutineConsultationRepository):
    """In-memory repository wired through FastAPI dependency overrides."""

    def __init__(
        self,
        routines: list[Routine] | None = None,
        authorized: dict[tuple[int, int], bool] | None = None,
    ) -> None:
        self._routines = list(routines or [])
        self._authorized = dict(authorized or {})

    async def is_authorized_for_program(
        self,
        id_trainer: int,
        id_workout_program: int,
        on_date,
    ) -> bool:
        return self._authorized.get((id_trainer, id_workout_program), False)

    async def list_for_trainer(
        self,
        id_trainer: int,
        id_workout_program: int,
        on_date,
    ) -> list[Routine]:
        return [
            r
            for r in self._routines
            if r.id_workout_program == id_workout_program
            and r.id_trainer_creator != id_trainer
        ]


def _make_routine(
    id_routine: int,
    id_workout_program: int,
    id_trainer_creator: int,
    status: RoutineStatus = RoutineStatus.APPROVED,
    creation_date=None,
) -> Routine:
    from datetime import date

    return Routine(
        id_routine=id_routine,
        id_workout_program=id_workout_program,
        id_trainer_creator=id_trainer_creator,
        status=status,
        creation_date=creation_date or date(2026, 1, 10),
    )


class RoutineConsultationApiIntegrationTests(unittest.TestCase):
    """Tests for ``GET /training-programs/{id}/routines`` through TestClient."""

    def setUp(self) -> None:
        self.trainer_a = ActorDTO(id_user=1, role=UserRole.TRAINER)
        self.trainer_b = ActorDTO(id_user=2, role=UserRole.TRAINER)
        self.admin = ActorDTO(id_user=4, role=UserRole.ADMIN)

        self.program_a = 10
        self.program_b = 20

        self.routines = [
            _make_routine(1, self.program_a, self.trainer_a.id_user),
            _make_routine(2, self.program_a, self.trainer_b.id_user),
            _make_routine(3, self.program_b, self.trainer_b.id_user),
        ]

        self.client = TestClient(app)

    def _override(
        self,
        actor: ActorDTO,
        authorized: dict[tuple[int, int], bool] | None = None,
    ) -> None:
        if authorized is None:
            authorized = {
                (actor.id_user, self.program_a): True,
            }
        repo = _FakeConsultationRepository(self.routines, authorized=authorized)
        app.dependency_overrides[get_current_actor] = lambda: actor
        from app.adapters.dependencies import (
            get_routine_consultation_repository,
            get_list_routines_for_trainer_use_case,
        )

        app.dependency_overrides[get_routine_consultation_repository] = (
            lambda: repo
        )
        app.dependency_overrides[get_list_routines_for_trainer_use_case] = (
            lambda: __import__(
                "app.application.use_cases.list_routines_for_trainer",
                fromlist=["ListRoutinesForTrainerUseCase"],
            ).ListRoutinesForTrainerUseCase(repo)
        )

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def _get(self, id_workout_program: int):
        return self.client.get(
            f"/api/v1/training-programs/{id_workout_program}/routines"
        )

    def test_trainer_in_same_program_sees_peer_routines(self) -> None:
        self._override(self.trainer_a)
        try:
            response = self._get(self.program_a)
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            # Only routine 2 (by trainer B) should be visible; routine 1 is
            # trainer A's own.
            self.assertEqual(len(body), 1)
            self.assertEqual(body[0]["id_routine"], 2)
            self.assertEqual(body[0]["id_trainer_creator"], self.trainer_b.id_user)
            self.assertEqual(body[0]["status"], "APPROVED")
            self.assertIn("creation_date", body[0])
        finally:
            app.dependency_overrides.clear()

    def test_trainer_not_authorized_receives_403(self) -> None:
        self._override(self.trainer_a, authorized={})
        try:
            response = self._get(self.program_a)
            self.assertEqual(response.status_code, 403, response.text)
        finally:
            app.dependency_overrides.clear()

    def test_trainer_cannot_consult_unrelated_program(self) -> None:
        # Trainer A is authorized only for program A; consulting program B
        # must be rejected (403), never expose routines from another program.
        self._override(
            self.trainer_a,
            authorized={(self.trainer_a.id_user, self.program_a): True},
        )
        try:
            response = self._get(self.program_b)
            self.assertEqual(response.status_code, 403, response.text)
        finally:
            app.dependency_overrides.clear()

    def test_non_trainer_actor_receives_403(self) -> None:
        self._override(self.admin)
        try:
            response = self._get(self.program_a)
            self.assertEqual(response.status_code, 403, response.text)
        finally:
            app.dependency_overrides.clear()

    def test_response_shape_matches_summary_dto(self) -> None:
        self._override(self.trainer_a)
        try:
            response = self._get(self.program_a)
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(len(body), 1)
            dto = RoutineSummaryDTO(**body[0])
            self.assertEqual(dto.id_routine, 2)
            self.assertEqual(dto.id_workout_program, self.program_a)
            self.assertEqual(dto.id_trainer_creator, self.trainer_b.id_user)
            self.assertIsInstance(dto.creation_date, str)
            self.assertEqual(dto.status, "APPROVED")
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
