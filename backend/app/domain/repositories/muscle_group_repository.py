"""Domain contract for muscle group catalog persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.muscle_group import MuscleGroup


class MuscleGroupRepository(ABC):
    """CRUD operations for the muscle group catalog."""

    @abstractmethod
    async def save(self, muscle_group: MuscleGroup) -> MuscleGroup:
        """Insert or update a muscle group."""

    @abstractmethod
    async def get_by_id(self, id_muscle_group: int) -> Optional[MuscleGroup]:
        """Return a muscle group by identifier, or ``None``."""

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[MuscleGroup]:
        """Return a muscle group by its normalized name, or ``None``."""

    @abstractmethod
    async def list(self) -> list[MuscleGroup]:
        """Return all muscle groups ordered by name."""

    @abstractmethod
    async def delete(self, id_muscle_group: int) -> None:
        """Delete a muscle group when no database relation references it."""
