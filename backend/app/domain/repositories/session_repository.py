"""Domain contract for training session persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from app.domain.entities.training_session import TrainingSession


class SessionRepository(ABC):
    """Persistence operations for sessions recorded against assignments."""

    @abstractmethod
    async def save(self, session: TrainingSession) -> TrainingSession:
        """Persist a training session and return it with its identifier."""

    @abstractmethod
    async def find_by_assignment_and_date(
        self, id_assignment: int, session_date: date
    ) -> Optional[TrainingSession]:
        """Return a session for an assignment and date, or ``None``."""

    @abstractmethod
    async def list_by_assignment(self, id_assignment: int) -> list[TrainingSession]:
        """Return all sessions recorded for an assignment."""
