"""Use case: rename a muscle group catalog entry (U-3)."""

from __future__ import annotations

from app.application.dto.muscle_group_dto import (
    MuscleGroupOutputDTO,
    UpdateMuscleGroupInputDTO,
)
from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.application.services.authorization import require_admin
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.muscle_group_repository import MuscleGroupRepository


class UpdateMuscleGroupUseCase:
    """Update the name of an existing muscle group."""

    def __init__(self, muscle_group_repository: MuscleGroupRepository) -> None:
        self._muscle_groups = muscle_group_repository

    async def execute(
        self, input_dto: UpdateMuscleGroupInputDTO
    ) -> MuscleGroupOutputDTO:
        require_admin(input_dto.actor, "update muscle groups")

        current = await self._muscle_groups.get_by_id(input_dto.id_muscle_group)
        if current is None:
            raise ResourceNotFound("muscle group", input_dto.id_muscle_group)

        duplicate = await self._muscle_groups.get_by_name(input_dto.name)
        if (
            duplicate is not None
            and duplicate.id_muscle_group != input_dto.id_muscle_group
        ):
            raise DuplicateResource(
                "muscle group",
                f"a muscle group with the name {input_dto.name!r} already exists",
                existing=duplicate,
            )

        try:
            updated = MuscleGroup(
                id_muscle_group=input_dto.id_muscle_group,
                name=input_dto.name,
            )
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        saved = await self._muscle_groups.save(updated)
        return MuscleGroupOutputDTO.from_entity(saved)
