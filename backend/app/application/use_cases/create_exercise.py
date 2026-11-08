"""Use case: register an exercise in the bank (RF-11, RF-12, RF-14).

Only a trainer may create exercises. The use case validates that the muscle
group exists, delegates the classification to the domain and rejects a
duplicate by normalized name plus muscle group, returning the existing exercise
as the duplicate context.
"""

from __future__ import annotations

from datetime import date

from app.application.dto.exercise_dto import CreateExerciseInputDTO, ExerciseOutputDTO
from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.domain.entities.exercise import Exercise
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.catalog_repository import CatalogRepository
from app.domain.repositories.exercise_repository import ExerciseRepository
from app.domain.value_objects.user_role import UserRole


class CreateExerciseUseCase:
    """Register an exercise authored by the authenticated trainer."""

    def __init__(
        self,
        exercise_repository: ExerciseRepository,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._exercises = exercise_repository
        self._catalogs = catalog_repository

    def execute(self, input_dto: CreateExerciseInputDTO) -> ExerciseOutputDTO:
        actor = input_dto.actor
        if actor.role is not UserRole.TRAINER:
            raise PermissionDenied(
                "only trainers can register exercises; "
                f"the actor has the role {actor.role.value}."
            )

        muscle_group = self._catalogs.get_muscle_group(input_dto.muscle_group_id)
        if muscle_group is None:
            raise ResourceNotFound("muscle group", input_dto.muscle_group_id)

        try:
            exercise = Exercise(
                name=input_dto.name,
                exercise_type=input_dto.exercise_type,
                intensity=input_dto.intensity,
                muscle_group=muscle_group,
                id_trainer_creator=actor.id_user,
                description=input_dto.description,
                registration_date=input_dto.registration_date or date.today(),
            )
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        duplicate = self._exercises.find_duplicate(
            exercise.normalized_name, muscle_group.id_muscle_group
        )
        if duplicate is not None:
            raise DuplicateResource(
                "exercise",
                "an exercise with the same name already exists in the muscle "
                f"group {muscle_group.name!r} "
                f"(id_exercise={duplicate.id_exercise}, name={duplicate.name!r}).",
                existing=duplicate,
            )

        saved = self._exercises.save(exercise)
        return ExerciseOutputDTO.from_entity(saved)
