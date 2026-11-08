"""Contract of the exercise repository.

The interface is expressed only with domain types: it contains no SQL, no
psycopg and no framework import. The adapter in the infrastructure layer is the
only place that knows about the ``exercise`` table.

The methods are coroutines because the persistence adapters use the async
psycopg pool of the infrastructure layer (E2-05).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.exercise import Exercise
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel

ORDERING_FIELDS = ("name", "registration_date", "id_exercise")


class ExerciseRepository(ABC):
    """Persistence operations required by the exercise use cases."""

    @abstractmethod
    async def save(self, exercise: Exercise) -> Exercise:
        """Insert the exercise when it has no identifier, update it otherwise.

        Returns the stored exercise, including the identifier assigned by the
        database.
        """

    @abstractmethod
    async def get_by_id(self, id_exercise: int) -> Optional[Exercise]:
        """Return the exercise with that identifier, or ``None``."""

    @abstractmethod
    async def find_duplicate(
        self, normalized_name: str, id_muscle_group: int
    ) -> Optional[Exercise]:
        """Return the exercise that collides with the duplicate key (U-12).

        Duplicate detection uses the normalized name and the muscle group, so
        the same name in another muscle group is not a duplicate.
        """

    @abstractmethod
    async def list(
        self,
        *,
        muscle_group_id: Optional[int] = None,
        exercise_type: Optional[ExerciseType] = None,
        intensity: Optional[IntensityLevel] = None,
        order_by: str = "name",
        descending: bool = False,
    ) -> list[Exercise]:
        """Return the exercises that match the optional filters (RF-13)."""
