"""Use case: deactivate an administrator-managed user account."""

from __future__ import annotations

from app.application.dto.user_dto import UpdateUserInputDTO, UserOutputDTO
from app.application.exceptions import ResourceNotFound
from app.application.use_cases.user.helpers import require_admin
from app.domain.repositories.user_repository import UserRepository


class DeactivateUserUseCase:
    """Deactivate an account without deleting its historical records."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def execute(self, input_dto: UpdateUserInputDTO) -> UserOutputDTO:
        require_admin(input_dto.actor)
        current = await self._users.get_by_id(input_dto.id_user)
        if current is None:
            raise ResourceNotFound("user", input_dto.id_user)

        deactivated = await self._users.deactivate(input_dto.id_user)
        profile = await self._users.get_profile(input_dto.id_user)
        return UserOutputDTO.from_entity(deactivated, profile)
