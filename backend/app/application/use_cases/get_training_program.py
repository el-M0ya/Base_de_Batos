"""Use case: retrieve one training program and its coverage."""

from __future__ import annotations

from app.application.dto.training_program_dto import TrainingProgramOutputDTO
from app.application.exceptions import ResourceNotFound
from app.domain.repositories.workout_program_repository import (
    WorkoutProgramRepository,
)


class GetTrainingProgramUseCase:
    """Return a training program with its covered muscle groups."""

    def __init__(self, program_repository: WorkoutProgramRepository) -> None:
        self._programs = program_repository

    async def execute(self, id_workout_program: int) -> TrainingProgramOutputDTO:
        program = await self._programs.get_by_id(id_workout_program)
        if program is None:
            raise ResourceNotFound("training program", id_workout_program)
        return TrainingProgramOutputDTO.from_entity(program)
