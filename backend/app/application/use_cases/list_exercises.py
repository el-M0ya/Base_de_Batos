"""Use case: list the exercise bank (RF-13).

Every authenticated user can consult the bank and combine the filters by muscle
group, exercise type and intensity, choosing the ordering field.
"""

from __future__ import annotations

from app.application.dto.exercise_dto import ExerciseOutputDTO, ListExercisesInputDTO
from app.application.exceptions import InvalidInput
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.exercise_repository import ORDERING_FIELDS, ExerciseRepository
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel


class ListExercisesUseCase:
    """Return the exercises that match the requested filters and ordering."""

    def __init__(self, exercise_repository: ExerciseRepository) -> None:
        self._exercises = exercise_repository

    def execute(self, input_dto: ListExercisesInputDTO) -> tuple[ExerciseOutputDTO, ...]:
        order_by = input_dto.order_by.strip().lower()
        if order_by not in ORDERING_FIELDS:
            raise InvalidInput(
                f"'order_by' must be one of {list(ORDERING_FIELDS)}, got "
                f"{input_dto.order_by!r}."
            )

        try:
            exercise_type = (
                ExerciseType.from_value(input_dto.exercise_type)
                if input_dto.exercise_type is not None
                else None
            )
            intensity = (
                IntensityLevel.from_value(input_dto.intensity)
                if input_dto.intensity is not None
                else None
            )
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        exercises = self._exercises.list(
            muscle_group_id=input_dto.muscle_group_id,
            exercise_type=exercise_type,
            intensity=intensity,
            order_by=order_by,
            descending=input_dto.descending,
        )
        return tuple(ExerciseOutputDTO.from_entity(exercise) for exercise in exercises)
