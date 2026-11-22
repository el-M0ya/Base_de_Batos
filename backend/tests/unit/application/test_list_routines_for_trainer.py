"""Unit tests for program-scoped peer routine consultation."""

from __future__ import annotations

import unittest
from datetime import date
import pathlib
import sys

# ``fakes`` is a sibling package of this test module.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from fakes.in_memory_routine_consultation_repository import (
    InMemoryRoutineConsultationRepository,
)

from app.application.dto.actor import ActorDTO
from app.application.dto.routine_dto import ListRoutinesForTrainerInputDTO
from app.application.exceptions import PermissionDenied
from app.application.use_cases.list_routines_for_trainer import (
    ListRoutinesForTrainerUseCase,
)
from app.domain.entities.authorisation import Authorisation
from app.domain.entities.routine import Routine, RoutineStatus


class ListRoutinesForTrainerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.consultation_date = date(2026, 6, 1)
        self.trainer = ActorDTO(id_user=10, role="TRAINER")
        authorisations = [
            Authorisation(10, 20, can_generate=True, start_date=date(2026, 1, 1)),
            Authorisation(11, 20, can_validate=True, start_date=date(2026, 1, 1)),
            Authorisation(12, 21, can_generate=True, start_date=date(2026, 1, 1)),
        ]
        routines = [
            Routine(
                id_routine=1,
                id_workout_program=20,
                id_trainer_creator=11,
                status=RoutineStatus.APPROVED,
                creation_date=date(2026, 5, 1),
            ),
            Routine(
                id_routine=2,
                id_workout_program=21,
                id_trainer_creator=12,
                creation_date=date(2026, 5, 2),
            ),
        ]
        repository = InMemoryRoutineConsultationRepository(routines, authorisations)
        self.use_case = ListRoutinesForTrainerUseCase(repository)

    async def test_lists_routines_from_another_trainer_in_same_program(self) -> None:
        result = await self.use_case.execute(
            ListRoutinesForTrainerInputDTO(
                actor=self.trainer,
                id_workout_program=20,
                on_date=self.consultation_date,
            )
        )

        self.assertEqual(
            [(routine.id_routine, routine.id_trainer_creator) for routine in result],
            [(1, 11)],
        )
        self.assertEqual(result[0].creation_date, date(2026, 5, 1))
        self.assertEqual(result[0].status, "APPROVED")

    async def test_does_not_expose_routines_from_another_program(self) -> None:
        result = await self.use_case.execute(
            ListRoutinesForTrainerInputDTO(
                actor=self.trainer,
                id_workout_program=20,
                on_date=self.consultation_date,
            )
        )

        self.assertNotIn(2, [routine.id_routine for routine in result])

    async def test_rejects_an_unauthorized_trainer(self) -> None:
        with self.assertRaises(PermissionDenied):
            await self.use_case.execute(
                ListRoutinesForTrainerInputDTO(
                    actor=ActorDTO(id_user=99, role="TRAINER"),
                    id_workout_program=20,
                    on_date=self.consultation_date,
                )
            )

    async def test_returns_empty_when_authorized_program_has_no_peer_routines(self) -> None:
        use_case = ListRoutinesForTrainerUseCase(
            InMemoryRoutineConsultationRepository(
                authorisations=[
                    Authorisation(
                        10,
                        22,
                        can_generate=True,
                        start_date=date(2026, 1, 1),
                    )
                ]
            )
        )

        result = await use_case.execute(
            ListRoutinesForTrainerInputDTO(
                actor=self.trainer,
                id_workout_program=22,
                on_date=self.consultation_date,
            )
        )

        self.assertEqual(result, ())

    async def test_returns_empty_when_creator_authorization_is_expired(self) -> None:
        repository = InMemoryRoutineConsultationRepository(
            routines=[
                Routine(
                    id_routine=3,
                    id_workout_program=20,
                    id_trainer_creator=11,
                )
            ],
            authorisations=[
                Authorisation(
                    10,
                    20,
                    can_generate=True,
                    start_date=date(2026, 1, 1),
                ),
                Authorisation(
                    11,
                    20,
                    can_validate=True,
                    start_date=date(2025, 1, 1),
                    end_date=date(2025, 12, 31),
                ),
            ],
        )

        result = await ListRoutinesForTrainerUseCase(repository).execute(
            ListRoutinesForTrainerInputDTO(
                actor=self.trainer,
                id_workout_program=20,
                on_date=self.consultation_date,
            )
        )

        self.assertEqual(result, ())

    async def test_non_trainers_cannot_consult_peer_routines(self) -> None:
        with self.assertRaises(PermissionDenied):
            await ListRoutinesForTrainerUseCase(
                InMemoryRoutineConsultationRepository()
            ).execute(
                ListRoutinesForTrainerInputDTO(
                    actor=ActorDTO(id_user=42, role="CLIENT"),
                    id_workout_program=20,
                )
            )
