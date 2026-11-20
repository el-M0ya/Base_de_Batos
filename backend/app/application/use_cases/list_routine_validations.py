"""Use case: retrieve the completed validations of a routine (RF-25, RI-20).

The history is returned in reverse chronological order, matching the
repository contract. A trainer needs a ``can_validate`` authorisation for the
routine's workout program that is effective today because the records contain
review decisions and observations.
"""

from __future__ import annotations

from datetime import date

from app.application.dto.routine_review_dto import (
    ListRoutineValidationsInputDTO,
    RoutineValidationOutputDTO,
)
from app.application.exceptions import ResourceNotFound
from app.application.services.authorization import require_validation_authorisation
from app.domain.repositories.authorisation_repository import AuthorisationRepository
from app.domain.repositories.routine_repository import RoutineRepository


class ListRoutineValidationsUseCase:
    """Return the validation history of a routine."""

    def __init__(
        self,
        routine_repository: RoutineRepository,
        authorisation_repository: AuthorisationRepository,
    ) -> None:
        self._routines = routine_repository
        self._authorisations = authorisation_repository

    async def execute(
        self, input_dto: ListRoutineValidationsInputDTO
    ) -> list[RoutineValidationOutputDTO]:
        """Load the routine, authorise the actor, and map its validation rows."""
        loaded = await self._routines.get_complete(input_dto.id_routine)
        if loaded is None:
            raise ResourceNotFound("routine", input_dto.id_routine)

        routine, _structure = loaded

        await require_validation_authorisation(
            input_dto.actor,
            routine.id_workout_program,
            date.today(),
            self._authorisations,
        )

        validations = await self._routines.list_validations(input_dto.id_routine)
        return [
            RoutineValidationOutputDTO.from_entity(validation)
            for validation in validations
        ]
