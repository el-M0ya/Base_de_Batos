"""Use case: replace the muscle-group coverage of a training program (RF-10)."""

from __future__ import annotations

from app.application.dto.training_program_dto import (
    SetTrainingProgramMuscleGroupsInputDTO,
    TrainingProgramOutputDTO,
)
from app.application.exceptions import ResourceNotFound
from app.application.services.authorization import require_admin
from app.application.services.muscle_group_resolver import MuscleGroupResolver
from app.domain.repositories.workout_program_repository import (
    WorkoutProgramRepository,
)


class SetTrainingProgramMuscleGroupsUseCase:
    """Replace all muscle groups covered by an existing training program."""

    def __init__(
        self,
        program_repository: WorkoutProgramRepository,
        muscle_group_resolver: MuscleGroupResolver,
    ) -> None:
        self._programs = program_repository
        self._muscle_groups = muscle_group_resolver

    async def execute(
        self, input_dto: SetTrainingProgramMuscleGroupsInputDTO
    ) -> TrainingProgramOutputDTO:
        require_admin(input_dto.actor, "change training program coverage")

        program = await self._programs.get_by_id(input_dto.id_workout_program)
        if program is None:
            raise ResourceNotFound("training program", input_dto.id_workout_program)

        program.target_muscle_groups = await self._muscle_groups.resolve(
            input_dto.muscle_group_ids
        )
        saved = await self._programs.save(program)
        return TrainingProgramOutputDTO.from_entity(saved)
