"""Persistence contract for program-scoped routine consultation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.routine import Routine


class RoutineConsultationRepository(ABC):
    """Read routines visible to a trainer in an authorized program."""

    @abstractmethod
    async def is_authorized_for_program(
        self,
        id_trainer: int,
        id_workout_program: int,
        on_date: date,
    ) -> bool:
        """Return whether the trainer serves the program on the supplied date."""

    @abstractmethod
    async def list_for_trainer(
        self,
        id_trainer: int,
        id_workout_program: int,
        on_date: date,
    ) -> list[Routine]:
        """Return routines from other authorized trainers in the program."""
