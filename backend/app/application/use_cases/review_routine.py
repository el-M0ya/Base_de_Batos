"""Use case: review a routine and persist the validation decision (RF-25, RF-26, R10).

The use case supports the two decisions defined by the domain: approval and
rejection. Both decisions are stored as a ``RoutineValidation`` record with the
reviewer, date, decision, and observations. A rejection requires non-empty
observations. The routine must be in ``PENDING_REVIEW`` and the validation date
cannot precede its creation date. The State pattern decides whether the
transition is allowed.

Only a trainer with an effective ``can_validate`` authorisation for the
routine's workout program can review it. The persisted authorisation is checked
on the validation date, so a capability cached in the actor at login time is
not trusted.

The E1-08 database trigger synchronises ``routine.status`` with the stored
decision inside the same transaction. The in-memory routine is transitioned
through the State pattern before saving so the returned status matches the
decision that was persisted.

OPEN DECISION (E7-01): the current ``ApprovedState`` declares no outgoing
transitions, so approval is terminal. If the team confirms that an approved
routine may be reviewed again, only the state class needs to change; this use
case follows the transition table automatically.
"""

from __future__ import annotations

from app.application.dto.routine_review_dto import (
    ReviewRoutineInputDTO,
    RoutineValidationOutputDTO,
)
from app.application.exceptions import InvalidInput, ResourceNotFound
from app.application.services.authorization import require_validation_authorisation
from app.domain.entities.routine_validation import RoutineValidation
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.authorisation_repository import AuthorisationRepository
from app.domain.repositories.routine_repository import RoutineRepository


class ReviewRoutineUseCase:
    """Approve or reject a pending routine on behalf of an authorised trainer."""

    def __init__(
        self,
        routine_repository: RoutineRepository,
        authorisation_repository: AuthorisationRepository,
    ) -> None:
        self._routines = routine_repository
        self._authorisations = authorisation_repository

    async def execute(
        self, input_dto: ReviewRoutineInputDTO
    ) -> RoutineValidationOutputDTO:
        """Record the decision and persist the resulting validation.

        The routine is loaded first because its workout program identifies the
        authorisation that the reviewer needs. The domain then checks the
        current state and the validation date before the State pattern applies
        the transition. Finally, the repository stores the validation; the
        E1-08 trigger updates ``routine.status`` in the same transaction.
        """
        loaded = await self._routines.get_complete(input_dto.id_routine)
        if loaded is None:
            raise ResourceNotFound("routine", input_dto.id_routine)

        routine, _structure = loaded

        await require_validation_authorisation(
            input_dto.actor,
            routine.id_workout_program,
            input_dto.validation_date,
            self._authorisations,
        )

        try:
            validation = RoutineValidation(
                id_routine=input_dto.id_routine,
                id_room_chief=input_dto.actor.id_user,
                decision=input_dto.decision,
                validation_date=input_dto.validation_date,
                observations=input_dto.observations,
            )

            # Validate the current state and date before mutating the routine.
            validation.validate_for(routine)

            # Delegate the lifecycle change to the State pattern. Approval and
            # rejection are the only transitions exposed by this use case.
            if validation.is_approval():
                routine.approve()
            else:
                routine.reject(validation.observations)
        except DomainException as error:
            # Keep domain errors behind the application boundary.
            raise InvalidInput(str(error)) from error

        # Do not persist routine.status before this call: the E1-08 trigger
        # requires the stored routine to still be PENDING_REVIEW when the
        # validation row is inserted, and it copies the decision into the
        # routine status inside the same transaction.
        saved = await self._routines.save_validation(validation)
        return RoutineValidationOutputDTO.from_entity(saved, routine.status)
