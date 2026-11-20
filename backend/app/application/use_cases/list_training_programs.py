"""Use case: list training programs with their coverage."""

from __future__ import annotations

from app.application.dto.training_program_dto import TrainingProgramOutputDTO
from app.domain.repositories.workout_program_repository import (
    WorkoutProgramRepository,
)


class ListTrainingProgramsUseCase:
    """Return every training program ordered by name."""

    def __init__(self, program_repository: WorkoutProgramRepository) -> None:
        self._programs = program_repository

    async def execute(self) -> list[TrainingProgramOutputDTO]:
        programs = await self._programs.list()
        return [TrainingProgramOutputDTO.from_entity(program) for program in programs]
