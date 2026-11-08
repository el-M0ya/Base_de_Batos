"""Use case: expose the catalogs required by the exercise form selectors."""

from __future__ import annotations

from app.application.dto.actor import ActorDTO
from app.application.dto.exercise_dto import CatalogOutputDTO, MuscleGroupDTO
from app.application.exceptions import InvalidInput
from app.domain.repositories.catalog_repository import CatalogRepository


class ListExerciseCatalogsUseCase:
    """Return muscle groups, exercise types and intensity levels."""

    def __init__(self, catalog_repository: CatalogRepository) -> None:
        self._catalogs = catalog_repository

    def execute(self, actor: ActorDTO) -> CatalogOutputDTO:
        if not isinstance(actor, ActorDTO):
            raise InvalidInput("an authenticated actor is required to read the catalogs.")

        muscle_groups = tuple(
            MuscleGroupDTO(
                id_muscle_group=muscle_group.id_muscle_group,
                name=muscle_group.name,
            )
            for muscle_group in self._catalogs.list_muscle_groups()
        )
        return CatalogOutputDTO(
            muscle_groups=muscle_groups,
            exercise_types=tuple(
                exercise_type.value
                for exercise_type in self._catalogs.list_exercise_types()
            ),
            intensity_levels=tuple(
                intensity.value
                for intensity in self._catalogs.list_intensity_levels()
            ),
        )
