"""Use case: list the muscle group catalog."""

from __future__ import annotations

from app.application.dto.muscle_group_dto import MuscleGroupOutputDTO
from app.domain.repositories.muscle_group_repository import MuscleGroupRepository


class ListMuscleGroupsUseCase:
    """Return every muscle group ordered by name."""

    def __init__(self, muscle_group_repository: MuscleGroupRepository) -> None:
        self._muscle_groups = muscle_group_repository

    async def execute(self) -> list[MuscleGroupOutputDTO]:
        groups = await self._muscle_groups.list()
        return [MuscleGroupOutputDTO.from_entity(group) for group in groups]
