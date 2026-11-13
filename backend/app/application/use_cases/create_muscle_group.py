"""Use case: create a muscle group catalog entry (U-3)."""

from __future__ import annotations

from app.application.dto.muscle_group_dto import (
    CreateMuscleGroupInputDTO,
    MuscleGroupOutputDTO,
)
from app.application.exceptions import DuplicateResource, InvalidInput
from app.application.services.authorization import require_admin
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.muscle_group_repository import MuscleGroupRepository


class CreateMuscleGroupUseCase:
    """Register a new muscle group. Only administrators may do it."""

    def __init__(self, muscle_group_repository: MuscleGroupRepository) -> None:
        self._muscle_groups = muscle_group_repository

    async def execute(
        self, input_dto: CreateMuscleGroupInputDTO
    ) -> MuscleGroupOutputDTO:
        require_admin(input_dto.actor, "create muscle groups")

        existing = await self._muscle_groups.get_by_name(input_dto.name)
        if existing is not None:
            raise DuplicateResource(
                "muscle group",
                f"a muscle group with the name {input_dto.name!r} already exists",
                existing=existing,
            )

        try:
            muscle_group = MuscleGroup(
                id_muscle_group=None,
                name=input_dto.name,
            )
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        saved = await self._muscle_groups.save(muscle_group)
        return MuscleGroupOutputDTO.from_entity(saved)
