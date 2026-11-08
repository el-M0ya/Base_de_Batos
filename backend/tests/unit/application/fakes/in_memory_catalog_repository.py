"""In-memory implementation of ``CatalogRepository`` for unit tests."""

from __future__ import annotations

from typing import Optional

from app.domain.entities.muscle_group import MuscleGroup
from app.domain.repositories.catalog_repository import CatalogRepository
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel


class InMemoryCatalogRepository(CatalogRepository):
    """Catalog repository backed by a list of muscle groups."""

    def __init__(self, muscle_groups: Optional[list[MuscleGroup]] = None) -> None:
        self._muscle_groups: list[MuscleGroup] = list(muscle_groups or [])

    def list_muscle_groups(self) -> list[MuscleGroup]:
        return sorted(self._muscle_groups, key=lambda group: group.name)

    def get_muscle_group(self, id_muscle_group: int) -> Optional[MuscleGroup]:
        for group in self._muscle_groups:
            if group.id_muscle_group == id_muscle_group:
                return group
        return None

    def list_exercise_types(self) -> list[ExerciseType]:
        return list(ExerciseType)

    def list_intensity_levels(self) -> list[IntensityLevel]:
        return list(IntensityLevel)
