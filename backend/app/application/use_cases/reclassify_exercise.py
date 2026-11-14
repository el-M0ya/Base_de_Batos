"""Use case: reclassify an existing exercise (RF-15, R1, R2, U-12).

Only the trainer who created the exercise may change its muscle group, type and
intensity. The use case validates the selected catalog values, preserves the
normalized-name plus muscle-group uniqueness rule and keeps the original
identity and authorship untouched.
"""

from __future__ import annotations

from app.application.dto.exercise_dto import (
    ExerciseOutputDTO,
    ReclassifyExerciseInputDTO,
)
from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.catalog_repository import CatalogRepository
from app.domain.repositories.exercise_repository import ExerciseRepository
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.domain.value_objects.user_role import UserRole


class ReclassifyExerciseUseCase:
    """Change the classification of an exercise authored by the actor."""

    def __init__(
        self,
        exercise_repository: ExerciseRepository,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._exercises = exercise_repository
        self._catalogs = catalog_repository

    async def execute(self, input_dto: ReclassifyExerciseInputDTO) -> ExerciseOutputDTO:
        actor = input_dto.actor

        # R2: administrators and clients can read the exercise bank but cannot
        # modify an exercise. The role check runs before any lookup so these
        # callers always receive a permission error.
        if actor.role is not UserRole.TRAINER:
            raise PermissionDenied(
                "only the trainer who created the exercise can reclassify it; "
                f"the actor has the role {actor.role.value}."
            )

        exercise = await self._exercises.get_by_id(input_dto.id_exercise)
        if exercise is None:
            raise ResourceNotFound("exercise", input_dto.id_exercise)

        # RF-15: another trainer may read the exercise but cannot modify it.
        if not exercise.is_authored_by(actor.id_user):
            raise PermissionDenied(
                "only the trainer who created the exercise can reclassify it."
            )

        muscle_group = await self._catalogs.get_muscle_group(input_dto.muscle_group_id)
        if muscle_group is None:
            raise ResourceNotFound("muscle group", input_dto.muscle_group_id)

        try:
            exercise_type = ExerciseType.from_value(input_dto.exercise_type)
            intensity = IntensityLevel.from_value(input_dto.intensity)
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        # Validate the selected values against the catalog exposed by the
        # repository, not only against the enum aliases.
        available_types = await self._catalogs.list_exercise_types()
        if exercise_type not in available_types:
            raise InvalidInput(
                f"exercise type {exercise_type.value!r} is not available in the "
                "catalog."
            )

        available_intensities = await self._catalogs.list_intensity_levels()
        if intensity not in available_intensities:
            raise InvalidInput(
                f"intensity {intensity.value!r} is not available in the catalog."
            )

        try:
            reclassified = exercise.reclassify(
                exercise_type=exercise_type,
                intensity=intensity,
                muscle_group=muscle_group,
            )
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        duplicate = await self._exercises.find_duplicate(
            reclassified.normalized_name,
            muscle_group.id_muscle_group,
            exclude_id=exercise.id_exercise,
        )
        if duplicate is not None:
            raise DuplicateResource(
                "exercise",
                "an exercise with the same name already exists in the muscle "
                f"group {muscle_group.name!r} "
                f"(id_exercise={duplicate.id_exercise}, name={duplicate.name!r}).",
                existing=duplicate,
            )

        saved = await self._exercises.save(reclassified)
        return ExerciseOutputDTO.from_entity(saved)
