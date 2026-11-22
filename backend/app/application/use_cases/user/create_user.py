"""Use case: create an administrator-managed user account."""

from __future__ import annotations

from app.application.dto.user_dto import CreateUserInputDTO, UserOutputDTO
from app.application.exceptions import DuplicateResource
from app.application.use_cases.user.helpers import (
    attach_profile_id,
    build_profile,
    build_user,
    require_admin,
)
from app.domain.repositories.user_repository import UserRepository


class CreateUserUseCase:
    """Create a user and its specialization profile atomically."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def execute(self, input_dto: CreateUserInputDTO) -> UserOutputDTO:
        require_admin(input_dto.actor)

        duplicate = await self._users.get_by_email(input_dto.email)
        if duplicate is not None:
            raise DuplicateResource(
                "user",
                f"email {input_dto.email!r} is already registered.",
                existing=duplicate,
            )

        user = build_user(input_dto)
        profile = build_profile(user, input_dto.trainer, input_dto.client)
        saved = await self._users.save(user, profile)
        profile = attach_profile_id(profile, saved)
        return UserOutputDTO.from_entity(saved, profile)
