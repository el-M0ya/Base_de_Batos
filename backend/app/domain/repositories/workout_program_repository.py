"""Domain contract for workout program persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from app.domain.entities.authorisation import Authorisation
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.workout_program import WorkoutProgram


class WorkoutProgramRepository(ABC):
    """Persistence operations for programs and their domain relationships."""

    @abstractmethod
    async def save(self, program: WorkoutProgram) -> WorkoutProgram:
        """Insert or update a program together with its covered groups."""

    @abstractmethod
    async def get_by_id(self, id_workout_program: int) -> Optional[WorkoutProgram]:
        """Return a program by identifier, or ``None``."""

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[WorkoutProgram]:
        """Return a program by its normalized name, or ``None``."""

    @abstractmethod
    async def list(self) -> list[WorkoutProgram]:
        """Return all workout programs ordered by name."""

    @abstractmethod
    async def delete(self, id_workout_program: int) -> None:
        """Delete a program and its coverage, preserving referential integrity."""

    @abstractmethod
    async def list_covered_muscle_groups(
        self, id_workout_program: int
    ) -> list[MuscleGroup]:
        """Return the muscle groups covered by a program."""

    @abstractmethod
    async def is_client_enrolled(
        self, id_client: int, id_workout_program: int, on_date: Optional[date] = None
    ) -> bool:
        """Return whether a client is enrolled in a program."""

    @abstractmethod
    async def get_authorisation(
        self, id_trainer: int, id_workout_program: int
    ) -> Optional[Authorisation]:
        """Return a trainer's authorization for a program, or ``None``."""
