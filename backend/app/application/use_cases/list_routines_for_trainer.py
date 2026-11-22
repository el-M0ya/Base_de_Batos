"""Use case for consulting routines from other trainers in one program."""

from __future__ import annotations

from datetime import date

from app.application.dto.routine_dto import (
    ListRoutinesForTrainerInputDTO,
    RoutineSummaryDTO,
)
from app.application.exceptions import PermissionDenied
from app.domain.repositories.routine_consultation_repository import (
    RoutineConsultationRepository,
)
from app.domain.value_objects.user_role import UserRole


class ListRoutinesForTrainerUseCase:
    """List routines visible to an authorized trainer in a program."""

    def __init__(self, routine_repository: RoutineConsultationRepository) -> None:
        self._routines = routine_repository

    async def execute(
        self, input_dto: ListRoutinesForTrainerInputDTO
    ) -> tuple[RoutineSummaryDTO, ...]:
        if input_dto.actor.role is not UserRole.TRAINER:
            raise PermissionDenied("only trainers can consult peer routines")

        on_date = input_dto.on_date or date.today()
        if not await self._routines.is_authorized_for_program(
            id_trainer=input_dto.actor.id_user,
            id_workout_program=input_dto.id_workout_program,
            on_date=on_date,
        ):
            raise PermissionDenied(
                "the trainer is not authorized for the requested program"
            )

        routines = await self._routines.list_for_trainer(
            id_trainer=input_dto.actor.id_user,
            id_workout_program=input_dto.id_workout_program,
            on_date=on_date,
        )
        return tuple(RoutineSummaryDTO.from_entity(routine) for routine in routines)
