"""Use case: delete a training program."""

from __future__ import annotations

from app.application.dto.training_program_dto import DeleteTrainingProgramInputDTO
from app.application.exceptions import ResourceNotFound
from app.application.services.authorization import require_admin
from app.domain.repositories.workout_program_repository import (
    WorkoutProgramRepository,
)


class DeleteTrainingProgramUseCase:
    """Delete a program and its coverage when no other relation references it."""

    def __init__(self, program_repository: WorkoutProgramRepository) -> None:
        self._programs = program_repository

    async def execute(self, input_dto: DeleteTrainingProgramInputDTO) -> None:
        require_admin(input_dto.actor, "delete training programs")

        current = await self._programs.get_by_id(input_dto.id_workout_program)
        if current is None:
            raise ResourceNotFound("training program", input_dto.id_workout_program)

        await self._programs.delete(input_dto.id_workout_program)
