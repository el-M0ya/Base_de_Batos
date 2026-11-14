"""Use case: update a training program and replace its coverage (RF-10)."""

from __future__ import annotations

from app.application.dto.training_program_dto import (
    TrainingProgramOutputDTO,
    UpdateTrainingProgramInputDTO,
)
from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.application.services.authorization import require_admin
from app.application.services.muscle_group_resolver import MuscleGroupResolver
from app.domain.entities.workout_program import WorkoutProgram
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.workout_program_repository import (
    WorkoutProgramRepository,
)


class UpdateTrainingProgramUseCase:
    """Update a training program and its associated muscle groups."""

    def __init__(
        self,
        program_repository: WorkoutProgramRepository,
        muscle_group_resolver: MuscleGroupResolver,
    ) -> None:
        self._programs = program_repository
        self._muscle_groups = muscle_group_resolver

    async def execute(
        self, input_dto: UpdateTrainingProgramInputDTO
    ) -> TrainingProgramOutputDTO:
        require_admin(input_dto.actor, "update training programs")

        current = await self._programs.get_by_id(input_dto.id_workout_program)
        if current is None:
            raise ResourceNotFound("training program", input_dto.id_workout_program)

        duplicate = await self._programs.get_by_name(input_dto.name)
        if (
            duplicate is not None
            and duplicate.id_workout_program != input_dto.id_workout_program
        ):
            raise DuplicateResource(
                "training program",
                f"a training program with the name {input_dto.name!r} already exists",
                existing=duplicate,
            )

        groups = await self._muscle_groups.resolve(input_dto.muscle_group_ids)
        try:
            updated = WorkoutProgram(
                name=input_dto.name,
                objective=input_dto.objective,
                id_workout_program=input_dto.id_workout_program,
                target_muscle_groups=groups,
            )
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        saved = await self._programs.save(updated)
        return TrainingProgramOutputDTO.from_entity(saved)
