"""Integration tests for the routine review use case against PostgreSQL.

The tests use the real SQL repositories. They assert that a review persists the
validation row and that the E1-08 trigger copies the decision into
``routine.status``. Invalid input and missing authorisation must not leave a
validation row behind.
"""

from __future__ import annotations

import asyncio
import unittest
from datetime import date
from decimal import Decimal

from psycopg import connect as _psycopg_connect

from backend.tests.integration.base import IntegrationTestCase
from backend.tests.integration.support.builders import (
    build_muscle_group,
    build_trainer,
    build_user,
    build_workout_program,
)
from backend.tests.integration.support.database import _target_db_dsn
from app.application.dto.actor import ActorDTO
from app.application.dto.routine_review_dto import (
    ListRoutineValidationsInputDTO,
    ReviewRoutineInputDTO,
)
from app.application.exceptions import InvalidInput, PermissionDenied
from app.application.use_cases.list_routine_validations import (
    ListRoutineValidationsUseCase,
)
from app.application.use_cases.review_routine import ReviewRoutineUseCase
from app.domain.entities.authorisation import Authorisation
from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.entities.routine_parameters import RoutineParameters
from app.domain.entities.routine_structure import (
    BlockType,
    RoutineBlock,
    RoutineStructure,
)
from app.domain.entities.routine_validation import ValidationDecision
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence.repositories.authorisation_repository_sql import (
    AuthorisationRepositorySql,
)
from app.infrastructure.persistence.repositories.routine_repository_sql import (
    RoutineRepositorySql,
)

CREATION_DATE = date(2026, 1, 1)
REVIEW_DATE = date(2026, 1, 2)


def _save_exercise_direct(
    id_exercise: int,
    name: str,
    muscle_group,
    id_trainer_creator: int,
) -> int:
    """Insert an exercise directly and return its identifier."""
    conn = _psycopg_connect(_target_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO exercise (id_exercise, name, description,
                    registration_date, id_exercise_type, id_muscle_group,
                    id_trainer_creator, intensity)
                VALUES (%s, %s, %s, %s,
                    (SELECT id_exercise_type FROM exercise_type WHERE name = %s),
                    %s, %s, %s)
                RETURNING id_exercise
                """,
                (
                    id_exercise,
                    name,
                    None,
                    CREATION_DATE,
                    "fuerza",
                    muscle_group.id_muscle_group,
                    id_trainer_creator,
                    "alto",
                ),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


class ReviewRoutineUseCaseIntegrationTests(IntegrationTestCase):
    """Persistence and status-consistency tests for the review use cases."""

    def setUp(self) -> None:
        super().setUp()
        self.trainer_id = 301
        trainer = build_user(
            id_user=self.trainer_id, name="Room Chief", role="TRAINER"
        )
        build_trainer(
            trainer, id_trainer=self.trainer_id, specialty="ROOM_CHIEF"
        )
        self.program_id = build_workout_program(id_workout_program=401)
        self.muscle_group = build_muscle_group(
            id_muscle_group=501, name="Pecho"
        )
        self.exercise_id = _save_exercise_direct(
            601, "Press de banca", self.muscle_group, self.trainer_id
        )
        self.actor = ActorDTO(
            id_user=self.trainer_id, role=UserRole.TRAINER
        )

    def _build_routine(self) -> Routine:
        """Build a complete routine header accepted by the SQL adapter."""
        routine = Routine(
            id_workout_program=self.program_id,
            id_trainer_creator=self.trainer_id,
            status=RoutineStatus.PENDING_REVIEW,
            creation_date=CREATION_DATE,
        )
        routine._parameters = RoutineParameters(
            id_routine=1,
            total_exercises=1,
            intensity_level="HIGH",
            cardio_ratio=Decimal("0"),
            strength_ratio=Decimal("100"),
        )
        routine._contains = [
            {
                "id_exercise": self.exercise_id,
                "execution_order": 1,
                "sets": 3,
                "repetitions": 10,
                "rest_time_seconds": 60,
            }
        ]
        return routine

    def _build_structure(self) -> RoutineStructure:
        """Build the JSONB structure that accompanies the routine header."""
        return RoutineStructure(
            id_routine=1,
            blocks=[
                RoutineBlock(
                    block_type=BlockType.SET,
                    order=1,
                    id_exercise=self.exercise_id,
                    sets=3,
                    repetitions=10,
                    rest_seconds=60,
                )
            ],
        )

    def test_approval_persists_validation_and_updates_status(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                routines = RoutineRepositorySql(tm)
                authorisations = AuthorisationRepositorySql(tm)
                await authorisations.create(
                    Authorisation(
                        id_trainer=self.trainer_id,
                        id_workout_program=self.program_id,
                        can_validate=True,
                        start_date=date(2020, 1, 1),
                    )
                )
                saved = await routines.save(
                    self._build_routine(), self._build_structure()
                )

                use_case = ReviewRoutineUseCase(routines, authorisations)
                result = await use_case.execute(
                    ReviewRoutineInputDTO(
                        actor=self.actor,
                        id_routine=saved.id_routine,
                        decision=ValidationDecision.APPROVED,
                        observations="The volume is adequate.",
                        validation_date=REVIEW_DATE,
                    )
                )

                self.assertEqual(result.routine_status, RoutineStatus.APPROVED)
                validations = await routines.list_validations(
                    saved.id_routine
                )
                self.assertEqual(len(validations), 1)
                self.assertEqual(
                    validations[0].decision, ValidationDecision.APPROVED
                )
                self.assertEqual(
                    validations[0].observations, "The volume is adequate."
                )

                stored = await routines.get_complete(saved.id_routine)
                self.assertIsNotNone(stored)
                self.assertEqual(stored[0].status, RoutineStatus.APPROVED)

                history = await ListRoutineValidationsUseCase(
                    routines, authorisations
                ).execute(
                    ListRoutineValidationsInputDTO(
                        actor=self.actor,
                        id_routine=saved.id_routine,
                    )
                )
                self.assertEqual(len(history), 1)
                self.assertEqual(
                    history[0].decision, ValidationDecision.APPROVED
                )

        asyncio.run(scenario())

    def test_rejection_persists_observations_and_updates_status(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                routines = RoutineRepositorySql(tm)
                authorisations = AuthorisationRepositorySql(tm)
                await authorisations.create(
                    Authorisation(
                        id_trainer=self.trainer_id,
                        id_workout_program=self.program_id,
                        can_validate=True,
                        start_date=date(2020, 1, 1),
                    )
                )
                saved = await routines.save(
                    self._build_routine(), self._build_structure()
                )

                use_case = ReviewRoutineUseCase(routines, authorisations)
                result = await use_case.execute(
                    ReviewRoutineInputDTO(
                        actor=self.actor,
                        id_routine=saved.id_routine,
                        decision=ValidationDecision.REJECTED,
                        observations="The volume is too high for the client.",
                        validation_date=REVIEW_DATE,
                    )
                )

                self.assertEqual(result.routine_status, RoutineStatus.REJECTED)
                validations = await routines.list_validations(
                    saved.id_routine
                )
                self.assertEqual(len(validations), 1)
                self.assertEqual(
                    validations[0].decision, ValidationDecision.REJECTED
                )
                self.assertEqual(
                    validations[0].observations,
                    "The volume is too high for the client.",
                )

                stored = await routines.get_complete(saved.id_routine)
                self.assertIsNotNone(stored)
                self.assertEqual(stored[0].status, RoutineStatus.REJECTED)

        asyncio.run(scenario())

    def test_rejection_without_observations_persists_nothing(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                routines = RoutineRepositorySql(tm)
                authorisations = AuthorisationRepositorySql(tm)
                await authorisations.create(
                    Authorisation(
                        id_trainer=self.trainer_id,
                        id_workout_program=self.program_id,
                        can_validate=True,
                        start_date=date(2020, 1, 1),
                    )
                )
                saved = await routines.save(
                    self._build_routine(), self._build_structure()
                )

                use_case = ReviewRoutineUseCase(routines, authorisations)
                with self.assertRaises(InvalidInput):
                    await use_case.execute(
                        ReviewRoutineInputDTO(
                            actor=self.actor,
                            id_routine=saved.id_routine,
                            decision=ValidationDecision.REJECTED,
                            observations=None,
                            validation_date=REVIEW_DATE,
                        )
                    )

                validations = await routines.list_validations(
                    saved.id_routine
                )
                self.assertEqual(validations, [])

                stored = await routines.get_complete(saved.id_routine)
                self.assertIsNotNone(stored)
                self.assertEqual(
                    stored[0].status, RoutineStatus.PENDING_REVIEW
                )

        asyncio.run(scenario())

    def test_missing_authorisation_persists_nothing(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                routines = RoutineRepositorySql(tm)
                authorisations = AuthorisationRepositorySql(tm)
                saved = await routines.save(
                    self._build_routine(), self._build_structure()
                )

                use_case = ReviewRoutineUseCase(routines, authorisations)
                with self.assertRaises(PermissionDenied):
                    await use_case.execute(
                        ReviewRoutineInputDTO(
                            actor=self.actor,
                            id_routine=saved.id_routine,
                            decision=ValidationDecision.APPROVED,
                            validation_date=REVIEW_DATE,
                        )
                    )

                validations = await routines.list_validations(
                    saved.id_routine
                )
                self.assertEqual(validations, [])

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
