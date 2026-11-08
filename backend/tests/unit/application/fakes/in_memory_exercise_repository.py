"""In-memory implementation of ``ExerciseRepository`` for unit tests.

It behaves like the PostgreSQL adapter for the rules exercised by the use
cases: identifiers are assigned on save and duplicate detection uses the
normalized name plus the muscle group.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from app.domain.entities.exercise import Exercise
from app.domain.repositories.exercise_repository import ExerciseRepository
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel


class InMemoryExerciseRepository(ExerciseRepository):
    """Dictionary-backed repository; no database, no psycopg."""

    def __init__(self, exercises: Optional[list[Exercise]] = None) -> None:
        self._rows: dict[int, Exercise] = {}
        self._next_id = 1
        for exercise in exercises or []:
            self.save_sync(exercise)

    # ------------------------------------------------------------------
    # ExerciseRepository
    # ------------------------------------------------------------------
    async def save(self, exercise: Exercise) -> Exercise:
        return self.save_sync(exercise)

    async def get_by_id(self, id_exercise: int) -> Optional[Exercise]:
        return self._rows.get(id_exercise)

    async def find_duplicate(
        self, normalized_name: str, id_muscle_group: int
    ) -> Optional[Exercise]:
        for exercise in self._rows.values():
            if (
                exercise.normalized_name == normalized_name
                and exercise.muscle_group.id_muscle_group == id_muscle_group
            ):
                return exercise
        return None

    async def list(
        self,
        *,
        muscle_group_id: Optional[int] = None,
        exercise_type: Optional[ExerciseType] = None,
        intensity: Optional[IntensityLevel] = None,
        order_by: str = "name",
        descending: bool = False,
    ) -> list[Exercise]:
        rows = [
            exercise
            for exercise in self._rows.values()
            if (muscle_group_id is None or exercise.belongs_to_muscle_group(muscle_group_id))
            and (exercise_type is None or exercise.exercise_type is exercise_type)
            and (intensity is None or exercise.intensity is intensity)
        ]
        keys = {
            "name": lambda exercise: exercise.normalized_name,
            "registration_date": lambda exercise: exercise.registration_date,
            "id_exercise": lambda exercise: exercise.id_exercise or 0,
        }
        return sorted(rows, key=keys[order_by], reverse=descending)

    # ------------------------------------------------------------------
    # Test helpers
    # ------------------------------------------------------------------
    def save_sync(self, exercise: Exercise) -> Exercise:
        """Synchronous save used to preload the repository in tests."""
        if exercise.id_exercise is None:
            saved = replace(exercise, id_exercise=self._next_id)
            self._next_id += 1
        else:
            saved = exercise
            self._next_id = max(self._next_id, saved.id_exercise + 1)
        self._rows[saved.id_exercise] = saved
        return saved

    def count(self) -> int:
        """Number of stored exercises."""
        return len(self._rows)
