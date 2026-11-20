"""Unit tests for ListRoutinesForTrainerUseCase (RF-19).

Uses an in-memory repository so no database is required.
"""

from __future__ import annotations

import asyncio
import unittest
from datetime import date

from app.application.dto.actor import ActorDTO
from app.application.dto.routine_dto import (
    ListRoutinesForTrainerInputDTO,
    RoutineSummaryDTO,
)
from app.application.exceptions import PermissionDenied
from app.application.use_cases.list_routines_for_trainer import (
    ListRoutinesForTrainerUseCase,
)
from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.repositories.routine_consultation_repository import (
    RoutineConsultationRepository,
)
from app.domain.value_objects.user_role import UserRole


class InMemoryRoutineConsultationRepository(RoutineConsultationRepository):
    """Dictionary-backed consultation repository for unit tests."""

    def __init__(
        self,
        routines: list[Routine] | None = None,
        authorisations: dict[tuple[int, int], bool] | None = None,
    ) -> None:
        self._routines: list[Routine] = list(routines or [])
        # (id_trainer, id_workout_program) -> authorized
        self._auth: dict[tuple[int, int], bool] = dict(authorisations or {})

    async def is_authorized_for_program(
        self,
        id_trainer: int,
        id_workout_program: int,
        on_date: date,
    ) -> bool:
        return self._auth.get((id_trainer, id_workout_program), False)

    async def list_for_trainer(
        self,
        id_trainer: int,
        id_workout_program: int,
        on_date: date,
    ) -> list[Routine]:
        return [
            r
            for r in self._routines
            if r.id_workout_program == id_workout_program
            and r.id_trainer_creator != id_trainer
        ]


class ListRoutinesForTrainerUseCaseTests(unittest.TestCase):
    """Tests for :class:`ListRoutinesForTrainerUseCase`."""

    def setUp(self) -> None:
        self.trainer_a = ActorDTO(id_user=1, role=UserRole.TRAINER)
        self.trainer_b = ActorDTO(id_user=2, role=UserRole.TRAINER)
        self.trainer_c = ActorDTO(id_user=3, role=UserRole.TRAINER)
        self.admin = ActorDTO(id_user=4, role=UserRole.ADMIN)
        self.client = ActorDTO(id_user=5, role=UserRole.CLIENT)

        self.program_a = 10
        self.program_b = 20

        self.routine_a1 = Routine(
            id_workout_program=self.program_a,
            id_trainer_creator=self.trainer_a.id_user,
            id_routine=1,
            status=RoutineStatus.APPROVED,
            creation_date=date(2026, 1, 10),
        )
        self.routine_a2 = Routine(
            id_workout_program=self.program_a,
            id_trainer_creator=self.trainer_b.id_user,
            id_routine=2,
            status=RoutineStatus.PENDING_REVIEW,
            creation_date=date(2026, 1, 11),
        )
        self.routine_b1 = Routine(
            id_workout_program=self.program_b,
            id_trainer_creator=self.trainer_c.id_user,
            id_routine=3,
            status=RoutineStatus.DRAFT,
            creation_date=date(2026, 1, 12),
        )

    def _repo(
        self,
        routines: list[Routine] | None = None,
        auth: dict[tuple[int, int], bool] | None = None,
    ) -> InMemoryRoutineConsultationRepository:
        return InMemoryRoutineConsultationRepository(routines, auth)

    def _use_case(
        self,
        routines: list[Routine] | None = None,
        auth: dict[tuple[int, int], bool] | None = None,
    ) -> ListRoutinesForTrainerUseCase:
        return ListRoutinesForTrainerUseCase(self._repo(routines, auth))

    def _run(self, coro):
        return asyncio.run(coro)

    def test_trainer_sees_peer_routines_in_same_program(self) -> None:
        # Trainer A is authorized for program A; trainer B created routines there.
        use_case = self._use_case(
            routines=[self.routine_a1, self.routine_a2],
            auth={
                (self.trainer_a.id_user, self.program_a): True,
                (self.trainer_b.id_user, self.program_a): True,
            },
        )
        result = self._run(
            use_case.execute(
                ListRoutinesForTrainerInputDTO(
                    actor=self.trainer_a,
                    id_workout_program=self.program_a,
                )
            )
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id_routine, 2)
        self.assertEqual(result[0].id_trainer_creator, self.trainer_b.id_user)
        self.assertEqual(result[0].status, "PENDING_REVIEW")
        self.assertIsInstance(result[0], RoutineSummaryDTO)

    def test_own_routine_is_excluded(self) -> None:
        # Trainer A should not see their own routine in program A.
        use_case = self._use_case(
            routines=[self.routine_a1, self.routine_a2],
            auth={
                (self.trainer_a.id_user, self.program_a): True,
                (self.trainer_b.id_user, self.program_a): True,
            },
        )
        result = self._run(
            use_case.execute(
                ListRoutinesForTrainerInputDTO(
                    actor=self.trainer_a,
                    id_workout_program=self.program_a,
                )
            )
        )
        ids = {r.id_routine for r in result}
        self.assertNotIn(1, ids)  # own routine excluded

    def test_trainer_not_authorized_for_program_is_denied(self) -> None:
        use_case = self._use_case(
            routines=[self.routine_a1, self.routine_a2],
            auth={},  # no authorizations
        )
        with self.assertRaises(PermissionDenied):
            self._run(
                use_case.execute(
                    ListRoutinesForTrainerInputDTO(
                        actor=self.trainer_a,
                        id_workout_program=self.program_a,
                    )
                )
            )

    def test_trainer_cannot_consult_unrelated_program(self) -> None:
        # Trainer A authorized only for program A; consulting program B must be
        # rejected, never expose routines from another program.
        use_case = self._use_case(
            routines=[self.routine_a1, self.routine_b1],
            auth={
                (self.trainer_a.id_user, self.program_a): True,
            },
        )
        with self.assertRaises(PermissionDenied):
            self._run(
                use_case.execute(
                    ListRoutinesForTrainerInputDTO(
                        actor=self.trainer_a,
                        id_workout_program=self.program_b,
                    )
                )
            )

    def test_non_trainer_actor_is_denied(self) -> None:
        use_case = self._use_case(routines=[self.routine_a1])
        for actor in (self.admin, self.client):
            with self.assertRaises(PermissionDenied):
                self._run(
                    use_case.execute(
                        ListRoutinesForTrainerInputDTO(
                            actor=actor,
                            id_workout_program=self.program_a,
                        )
                    )
                )

    def test_empty_program_returns_empty_tuple(self) -> None:
        use_case = self._use_case(
            routines=[],
            auth={
                (self.trainer_a.id_user, self.program_a): True,
            },
        )
        result = self._run(
            use_case.execute(
                ListRoutinesForTrainerInputDTO(
                    actor=self.trainer_a,
                    id_workout_program=self.program_a,
                )
            )
        )
        self.assertEqual(result, ())

    def test_result_includes_required_fields(self) -> None:
        use_case = self._use_case(
            routines=[self.routine_a2],
            auth={
                (self.trainer_a.id_user, self.program_a): True,
                (self.trainer_b.id_user, self.program_a): True,
            },
        )
        result = self._run(
            use_case.execute(
                ListRoutinesForTrainerInputDTO(
                    actor=self.trainer_a,
                    id_workout_program=self.program_a,
                )
            )
        )
        self.assertEqual(len(result), 1)
        dto = result[0]
        self.assertEqual(dto.id_routine, 2)
        self.assertEqual(dto.id_workout_program, self.program_a)
        self.assertEqual(dto.id_trainer_creator, self.trainer_b.id_user)
        self.assertEqual(dto.creation_date, date(2026, 1, 11))
        self.assertEqual(dto.status, "PENDING_REVIEW")


if __name__ == "__main__":
    unittest.main()
