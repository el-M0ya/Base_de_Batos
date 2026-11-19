"""Use case: create a training program with its muscle-group coverage (RF-10)."""

from __future__ import annotations

from app.application.dto.training_program_dto import (
    CreateTrainingProgramInputDTO,
    TrainingProgramOutputDTO,
)
from app.application.exceptions import DuplicateResource, InvalidInput
from app.application.services.authorization import require_admin
from app.application.services.muscle_group_resolver import MuscleGroupResolver
from app.domain.entities.workout_program import WorkoutProgram
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.workout_program_repository import (
    WorkoutProgramRepository,
)


class CreateTrainingProgramUseCase:
    """Register a training program and its covered muscle groups."""

    def __init__(
        self,
        program_repository: WorkoutProgramRepository,
        muscle_group_resolver: MuscleGroupResolver,
    ) -> None:
        self._programs = program_repository
        self._muscle_groups = muscle_group_resolver

    async def execute(
        self, input_dto: CreateTrainingProgramInputDTO
    ) -> TrainingProgramOutputDTO:
        require_admin(input_dto.actor, "create training programs")

        existing = await self._programs.get_by_name(input_dto.name)
        if existing is not None:
            raise DuplicateResource(
                "training program",
                f"a training program with the name {input_dto.name!r} already exists",
                existing=existing,
            )

        groups = await self._muscle_groups.resolve(input_dto.muscle_group_ids)
        try:
            program = WorkoutProgram(
                name=input_dto.name,
                objective=input_dto.objective,
                target_muscle_groups=groups,
            )
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        saved = await self._programs.save(program)
        return TrainingProgramOutputDTO.from_entity(saved)
