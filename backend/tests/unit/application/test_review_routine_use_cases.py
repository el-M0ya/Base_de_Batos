"""Unit tests for routine review and validation-history use cases (E7-01).

The tests use in-memory repositories and the application/domain layers only.
No FastAPI, psycopg, or PostgreSQL module is imported.
"""

from __future__ import annotations

import pathlib
import sys
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from fakes.in_memory_authorisation_repository import (
    InMemoryAuthorisationRepository,
)
from fakes.in_memory_routine_repository import InMemoryRoutineRepository

from app.application.dto.actor import ActorDTO, CapabilitiesDTO
from app.application.dto.routine_review_dto import (
    ListRoutineValidationsInputDTO,
    ReviewRoutineInputDTO,
)
from app.application.exceptions import (
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.application.use_cases.list_routine_validations import (
    ListRoutineValidationsUseCase,
)
from app.application.use_cases.review_routine import ReviewRoutineUseCase
from app.domain.entities.authorisation import Authorisation
from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.entities.routine_structure import RoutineStructure
from app.domain.entities.routine_validation import (
    RoutineValidation,
    ValidationDecision,
)
from app.domain.value_objects.user_role import UserRole

TRAINER_ID = 10
PROGRAM_ID = 100
ROUTINE_ID = 1
CREATION_DATE = date(2026, 1, 1)
REVIEW_DATE = date(2026, 1, 2)


def _routine(
    status: RoutineStatus = RoutineStatus.PENDING_REVIEW,
    creation_date: date = CREATION_DATE,
) -> Routine:
    """Build a routine header suitable for the review use cases."""
    return Routine(
        id_workout_program=PROGRAM_ID,
        id_trainer_creator=20,
        id_routine=ROUTINE_ID,
        status=status,
        creation_date=creation_date,
    )


def _structure() -> RoutineStructure:
    """Build the routine structure required by the complete-routine contract."""
    return RoutineStructure(id_routine=ROUTINE_ID, blocks=[])


def _trainer(can_validate: bool = True) -> ActorDTO:
    """Build a trainer actor; the persisted grant remains authoritative."""
    return ActorDTO(
        id_user=TRAINER_ID,
        role=UserRole.TRAINER,
        capabilities=CapabilitiesDTO(can_validate=can_validate),
    )


def _authorisation(**overrides) -> Authorisation:
    """Build an active trainer-program authorisation with validation rights."""
    values = {
        "id_trainer": TRAINER_ID,
        "id_workout_program": PROGRAM_ID,
        "can_generate": False,
        "can_validate": True,
        # Use a date safely in the past so the history check (today) passes.
        "start_date": date(2020, 1, 1),
        "end_date": None,
    }
    values.update(overrides)
    return Authorisation(**values)


class ReviewRoutineUseCaseTests(unittest.IsolatedAsyncioTestCase):
    """Approval, rejection, authorisation, and state rules."""

    def setUp(self) -> None:
        self.routines = InMemoryRoutineRepository([(_routine(), _structure())])
        self.authorisations = InMemoryAuthorisationRepository([_authorisation()])
        self.use_case = ReviewRoutineUseCase(
            self.routines, self.authorisations
        )

    async def _review(
        self,
        decision: ValidationDecision,
        *,
        observations: str | None = None,
        actor: ActorDTO | None = None,
        validation_date: date = REVIEW_DATE,
        id_routine: int = ROUTINE_ID,
    ):
        """Execute the use case with the supplied decision."""
        return await self.use_case.execute(
            ReviewRoutineInputDTO(
                actor=actor or _trainer(),
                id_routine=id_routine,
                decision=decision,
                observations=observations,
                validation_date=validation_date,
            )
        )

    async def test_trainer_with_authorisation_can_approve_routine(self) -> None:
        result = await self._review(
            ValidationDecision.APPROVED, observations="The volume is adequate."
        )

        self.assertIsNotNone(result.id_validation)
        self.assertEqual(result.id_routine, ROUTINE_ID)
        self.assertEqual(result.id_room_chief, TRAINER_ID)
        self.assertEqual(result.decision, ValidationDecision.APPROVED)
        self.assertEqual(result.observations, "The volume is adequate.")
        self.assertEqual(result.routine_status, RoutineStatus.APPROVED)

        stored = await self.routines.get_complete(ROUTINE_ID)
        self.assertIsNotNone(stored)
        self.assertEqual(stored[0].status, RoutineStatus.APPROVED)

        validations = await self.routines.list_validations(ROUTINE_ID)
        self.assertEqual(len(validations), 1)

    async def test_trainer_with_authorisation_can_reject_with_observations(
        self,
    ) -> None:
        result = await self._review(
            ValidationDecision.REJECTED,
            observations="The volume is too high for the client.",
        )

        self.assertEqual(result.decision, ValidationDecision.REJECTED)
        self.assertEqual(
            result.observations, "The volume is too high for the client."
        )
        self.assertEqual(result.routine_status, RoutineStatus.REJECTED)

        stored = await self.routines.get_complete(ROUTINE_ID)
        self.assertIsNotNone(stored)
        self.assertEqual(stored[0].status, RoutineStatus.REJECTED)

    async def test_rejection_without_observations_is_rejected(self) -> None:
        with self.assertRaises(InvalidInput):
            await self._review(ValidationDecision.REJECTED)

        validations = await self.routines.list_validations(ROUTINE_ID)
        self.assertEqual(validations, [])

        stored = await self.routines.get_complete(ROUTINE_ID)
        self.assertIsNotNone(stored)
        self.assertEqual(stored[0].status, RoutineStatus.PENDING_REVIEW)

    async def test_non_trainer_cannot_review(self) -> None:
        administrator = ActorDTO(id_user=1, role=UserRole.ADMIN)

        with self.assertRaises(PermissionDenied):
            await self._review(
                ValidationDecision.APPROVED, actor=administrator
            )

    async def test_trainer_without_authorisation_cannot_review(self) -> None:
        self.authorisations = InMemoryAuthorisationRepository()
        self.use_case = ReviewRoutineUseCase(
            self.routines, self.authorisations
        )

        with self.assertRaises(PermissionDenied):
            await self._review(ValidationDecision.APPROVED)

    async def test_generation_only_authorisation_cannot_review(self) -> None:
        self.authorisations = InMemoryAuthorisationRepository(
            [_authorisation(can_generate=True, can_validate=False)]
        )
        self.use_case = ReviewRoutineUseCase(
            self.routines, self.authorisations
        )

        with self.assertRaises(PermissionDenied):
            await self._review(ValidationDecision.APPROVED)

    async def test_expired_authorisation_cannot_review(self) -> None:
        self.authorisations = InMemoryAuthorisationRepository(
            [
                _authorisation(
                    start_date=date(2025, 1, 1),
                    end_date=date(2026, 1, 1),
                )
            ]
        )
        self.use_case = ReviewRoutineUseCase(
            self.routines, self.authorisations
        )

        with self.assertRaises(PermissionDenied):
            await self._review(ValidationDecision.APPROVED)

    async def test_persisted_authorisation_overrides_stale_capability(
        self,
    ) -> None:
        # A token issued before a grant was created may carry can_validate=False.
        # The persisted authorisation is the source of truth for the review.
        result = await self._review(
            ValidationDecision.APPROVED, actor=_trainer(can_validate=False)
        )

        self.assertEqual(result.decision, ValidationDecision.APPROVED)

    async def test_missing_routine_is_reported(self) -> None:
        with self.assertRaises(ResourceNotFound):
            await self._review(
                ValidationDecision.APPROVED, id_routine=999
            )

    async def test_routine_not_pending_cannot_be_reviewed(self) -> None:
        self.routines = InMemoryRoutineRepository(
            [(_routine(status=RoutineStatus.DRAFT), _structure())]
        )
        self.use_case = ReviewRoutineUseCase(
            self.routines, self.authorisations
        )

        with self.assertRaises(InvalidInput):
            await self._review(ValidationDecision.APPROVED)

    async def test_approved_routine_cannot_be_reviewed_again(self) -> None:
        # ApprovedState is terminal by the current State-pattern decision.
        self.routines = InMemoryRoutineRepository(
            [(_routine(status=RoutineStatus.APPROVED), _structure())]
        )
        self.use_case = ReviewRoutineUseCase(
            self.routines, self.authorisations
        )

        with self.assertRaises(InvalidInput):
            await self._review(ValidationDecision.APPROVED)

    async def test_rejected_routine_must_be_resubmitted_before_review(
        self,
    ) -> None:
        self.routines = InMemoryRoutineRepository(
            [(_routine(status=RoutineStatus.REJECTED), _structure())]
        )
        self.use_case = ReviewRoutineUseCase(
            self.routines, self.authorisations
        )

        with self.assertRaises(InvalidInput):
            await self._review(ValidationDecision.APPROVED)

    async def test_validation_date_before_creation_is_rejected(self) -> None:
        self.routines = InMemoryRoutineRepository(
            [(_routine(creation_date=date(2026, 1, 10)), _structure())]
        )
        self.use_case = ReviewRoutineUseCase(
            self.routines, self.authorisations
        )

        with self.assertRaises(InvalidInput):
            await self._review(
                ValidationDecision.APPROVED,
                validation_date=date(2026, 1, 1),
            )


class ListRoutineValidationsUseCaseTests(unittest.IsolatedAsyncioTestCase):
    """Validation-history retrieval and its authorisation check."""

    def setUp(self) -> None:
        self.routines = InMemoryRoutineRepository([(_routine(), _structure())])
        self.authorisations = InMemoryAuthorisationRepository([_authorisation()])
        self.use_case = ListRoutineValidationsUseCase(
            self.routines, self.authorisations
        )

    async def test_returns_completed_validations_newest_first(self) -> None:
        await self.routines.save_validation(
            RoutineValidation(
                id_routine=ROUTINE_ID,
                id_room_chief=TRAINER_ID,
                decision=ValidationDecision.REJECTED,
                validation_date=date(2026, 1, 2),
                observations="First review.",
            )
        )
        await self.routines.save_validation(
            RoutineValidation(
                id_routine=ROUTINE_ID,
                id_room_chief=TRAINER_ID,
                decision=ValidationDecision.APPROVED,
                validation_date=date(2026, 1, 3),
                observations="Second review.",
            )
        )

        result = await self.use_case.execute(
            ListRoutineValidationsInputDTO(
                actor=_trainer(),
                id_routine=ROUTINE_ID,
            )
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(
            [validation.decision for validation in result],
            [ValidationDecision.APPROVED, ValidationDecision.REJECTED],
        )
        self.assertIsNone(result[0].routine_status)

    async def test_missing_routine_is_reported(self) -> None:
        with self.assertRaises(ResourceNotFound):
            await self.use_case.execute(
                ListRoutineValidationsInputDTO(
                    actor=_trainer(), id_routine=999
                )
            )

    async def test_history_requires_validation_authorisation(self) -> None:
        self.authorisations = InMemoryAuthorisationRepository()
        self.use_case = ListRoutineValidationsUseCase(
            self.routines, self.authorisations
        )

        with self.assertRaises(PermissionDenied):
            await self.use_case.execute(
                ListRoutineValidationsInputDTO(
                    actor=_trainer(), id_routine=ROUTINE_ID
                )
            )


class RoutineReviewTransitionTests(unittest.TestCase):
    """The rejected-routine resubmission transition required by E7-01.

    Resubmission is already provided by the State pattern from E2-10. The
    review use case does not add a persistence operation for it because E7-01
    only lists approval, rejection, observations, and history retrieval.
    """

    def test_rejected_routine_can_return_to_pending_review(self) -> None:
        routine = _routine(status=RoutineStatus.REJECTED)

        routine.resubmit_for_review()

        self.assertEqual(routine.status, RoutineStatus.PENDING_REVIEW)


if __name__ == "__main__":
    unittest.main()
