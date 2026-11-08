"""Contract of the catalog repository.

Catalogs back the selectors of the exercise form and the existence checks done
before creating an exercise.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.muscle_group import MuscleGroup
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel


class CatalogRepository(ABC):
    """Read operations over the catalogs used by the exercise bank."""

    @abstractmethod
    def list_muscle_groups(self) -> list[MuscleGroup]:
        """Return every muscle group, ordered by name."""

    @abstractmethod
    def get_muscle_group(self, id_muscle_group: int) -> Optional[MuscleGroup]:
        """Return the muscle group with that identifier, or ``None``."""

    @abstractmethod
    def list_exercise_types(self) -> list[ExerciseType]:
        """Return the exercise types seeded in the catalog."""

    @abstractmethod
    def list_intensity_levels(self) -> list[IntensityLevel]:
        """Return the intensity levels seeded in the catalog."""
