"""Domain contract for routine persistence and validation history."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.routine import Routine
from app.domain.entities.routine_structure import RoutineStructure
from app.domain.entities.routine_validation import RoutineValidation


class RoutineRepository(ABC):
    """Persistence operations for complete routines and validations."""

    @abstractmethod
    async def save(
        self, routine: Routine, structure: RoutineStructure
    ) -> Routine:
        """Persist a routine with its complete variable structure."""

    @abstractmethod
    async def get_complete(
        self, id_routine: int
    ) -> Optional[tuple[Routine, RoutineStructure]]:
        """Return a routine and its complete structure, or ``None``."""

    @abstractmethod
    async def list_by_program(self, id_workout_program: int) -> list[Routine]:
        """Return routines belonging to a workout program."""

    @abstractmethod
    async def save_validation(
        self, validation: RoutineValidation
    ) -> RoutineValidation:
        """Persist a routine validation and return the stored entity."""

    @abstractmethod
    async def list_validations(self, id_routine: int) -> list[RoutineValidation]:
        """Return the validation history of a routine."""
