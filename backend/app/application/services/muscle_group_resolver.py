"""Application service that resolves muscle-group identifiers to entities."""

from __future__ import annotations

from collections.abc import Iterable

from app.application.exceptions import ResourceNotFound
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.repositories.muscle_group_repository import MuscleGroupRepository


class MuscleGroupResolver:
    """Load every requested group and fail when one does not exist."""

    def __init__(self, muscle_group_repository: MuscleGroupRepository) -> None:
        self._muscle_groups = muscle_group_repository

    async def resolve(self, ids: Iterable[int]) -> list[MuscleGroup]:
        """Return the groups in the requested order, without duplicates."""
        resolved: list[MuscleGroup] = []
        seen: set[int] = set()
        for identifier in ids:
            if identifier in seen:
                continue
            group = await self._muscle_groups.get_by_id(identifier)
            if group is None:
                raise ResourceNotFound("muscle group", identifier)
            seen.add(identifier)
            resolved.append(group)
        return resolved
