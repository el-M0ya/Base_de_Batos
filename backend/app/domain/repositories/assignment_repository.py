"""Domain contract for routine assignments."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from app.domain.entities.assignment import Assignment


class AssignmentRepository(ABC):
    """Persistence operations for assigning routines to clients."""

    @abstractmethod
    async def find_by_routine_and_client(
        self, id_routine: int, id_client: int
    ) -> Optional[Assignment]:
        """Return an assignment by routine and client, or ``None``."""

    @abstractmethod
    async def list_active_for_client(
        self, id_client: int, on_date: Optional[date] = None
    ) -> list[Assignment]:
        """Return a client's active assignments."""

    @abstractmethod
    async def save(self, assignment: Assignment) -> Assignment:
        """Persist an assignment and return it with its identifier."""
