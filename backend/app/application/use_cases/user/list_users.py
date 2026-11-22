"""Use case: list administrator-managed user accounts."""

from __future__ import annotations

from app.application.dto.actor import ActorDTO
from app.application.dto.user_dto import UserOutputDTO
from app.application.exceptions import InvalidInput
from app.application.use_cases.user.helpers import require_admin
from app.domain.repositories.user_repository import UserRepository


class ListUsersUseCase:
    """Return all user accounts to an administrator."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def execute(self, actor: ActorDTO) -> tuple[UserOutputDTO, ...]:
        require_admin(actor)
        users = await self._users.list_users()
        outputs: list[UserOutputDTO] = []
        for user in users:
            if user.id_user is None:
                raise InvalidInput("the user repository returned an unsaved user.")
            profile = await self._users.get_profile(user.id_user)
            outputs.append(UserOutputDTO.from_entity(user, profile))
        return tuple(outputs)
