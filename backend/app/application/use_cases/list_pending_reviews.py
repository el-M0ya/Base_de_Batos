"""Use case: list routines pending review for an authorised trainer.

The use case coordinates two collaborators:

* the authorisation repository, which supplies the programs the actor may
  validate;
* the routine repository, which lists routines belonging to each program.

Only routines in ``PENDING_REVIEW`` status for programs where the actor holds
an effective ``can_validate`` authorisation are returned.
"""

from __future__ import annotations

from datetime import date

from app.application.dto.actor import ActorDTO
from app.application.dto.routine_dto import RoutineSummaryDTO
from app.application.dto.routine_review_dto import ListPendingReviewsInputDTO
from app.domain.entities.routine import RoutineStatus
from app.domain.repositories.authorisation_repository import AuthorisationRepository
from app.domain.repositories.routine_repository import RoutineRepository


class ListPendingReviewsUseCase:
    """List routines pending review that the actor is authorised to validate."""

    def __init__(
        self,
        routine_repository: RoutineRepository,
        authorisation_repository: AuthorisationRepository,
    ) -> None:
        self._routines = routine_repository
        self._authorisations = authorisation_repository

    async def execute(
        self, input_dto: ListPendingReviewsInputDTO
    ) -> tuple[RoutineSummaryDTO, ...]:
        """Return routines pending review the actor may validate.

        For every program where the actor has an effective ``can_validate``
        grant today, load the program's routines and keep only those in
        ``PENDING_REVIEW`` status.
        """
        actor = input_dto.actor
        if not actor.is_trainer():
            from app.application.exceptions import PermissionDenied

            raise PermissionDenied(
                "only trainers with an effective can_validate authorisation "
                "can list pending routines; "
                f"the actor has the role {actor.role.value}."
            )

        authorisations = await self._authorisations.list(id_trainer=actor.id_user)
        today = date.today()

        pending: list[RoutineSummaryDTO] = []
        seen_program_ids: set[int] = set()

        for authorisation in authorisations:
            if not authorisation.can_validate:
                continue
            if not authorisation.is_active_on(today):
                continue

            program_id = authorisation.id_workout_program
            if program_id in seen_program_ids:
                continue
            seen_program_ids.add(program_id)

            routines = await self._routines.list_by_program(program_id)
            for routine in routines:
                if routine.status is RoutineStatus.PENDING_REVIEW:
                    pending.append(RoutineSummaryDTO.from_entity(routine))

        return tuple(pending)
