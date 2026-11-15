"""Use case: retrieve one muscle group catalog entry."""

from __future__ import annotations

from app.application.dto.muscle_group_dto import MuscleGroupOutputDTO
from app.application.exceptions import ResourceNotFound
from app.domain.repositories.muscle_group_repository import MuscleGroupRepository


class GetMuscleGroupUseCase:
    """Return a muscle group by identifier."""

    def __init__(self, muscle_group_repository: MuscleGroupRepository) -> None:
        self._muscle_groups = muscle_group_repository

    async def execute(self, id_muscle_group: int) -> MuscleGroupOutputDTO:
        muscle_group = await self._muscle_groups.get_by_id(id_muscle_group)
        if muscle_group is None:
            raise ResourceNotFound("muscle group", id_muscle_group)
        return MuscleGroupOutputDTO.from_entity(muscle_group)
