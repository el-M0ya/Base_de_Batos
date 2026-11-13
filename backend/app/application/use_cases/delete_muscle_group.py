"""Use case: delete a muscle group catalog entry."""

from __future__ import annotations

from app.application.dto.muscle_group_dto import DeleteMuscleGroupInputDTO
from app.application.exceptions import ResourceNotFound
from app.application.services.authorization import require_admin
from app.domain.repositories.muscle_group_repository import MuscleGroupRepository


class DeleteMuscleGroupUseCase:
    """Delete a muscle group only when no relation references it."""

    def __init__(self, muscle_group_repository: MuscleGroupRepository) -> None:
        self._muscle_groups = muscle_group_repository

    async def execute(self, input_dto: DeleteMuscleGroupInputDTO) -> None:
        require_admin(input_dto.actor, "delete muscle groups")

        current = await self._muscle_groups.get_by_id(input_dto.id_muscle_group)
        if current is None:
            raise ResourceNotFound("muscle group", input_dto.id_muscle_group)

        await self._muscle_groups.delete(input_dto.id_muscle_group)
