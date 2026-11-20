"""Use case: update an administrator-managed user account."""

from __future__ import annotations

from app.application.dto.user_dto import UpdateUserInputDTO, UserOutputDTO
from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    ResourceNotFound,
)
from app.application.use_cases.user.helpers import (
    attach_profile_id,
    build_account,
    build_profile,
    require_admin,
    validate_update_profile,
)
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.user_role import UserRole


class UpdateUserUseCase:
    """Update an account and an optional specialization profile atomically."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def execute(self, input_dto: UpdateUserInputDTO) -> UserOutputDTO:
        require_admin(input_dto.actor)

        current = await self._users.get_by_id(input_dto.id_user)
        if current is None:
            raise ResourceNotFound("user", input_dto.id_user)

        if input_dto.email is not None and input_dto.email != current.email:
            duplicate = await self._users.get_by_email(input_dto.email)
            if duplicate is not None and duplicate.id_user != current.id_user:
                raise DuplicateResource(
                    "user",
                    f"email {input_dto.email!r} is already registered.",
                    existing=duplicate,
                )

        role = (
            UserRole.from_value(input_dto.role)
            if input_dto.role is not None
            else current.role
        )
        validate_update_profile(role, input_dto.trainer, input_dto.client)
        if input_dto.role is not None and input_dto.role != current.role:
            if input_dto.trainer is None and input_dto.client is None:
                raise BusinessRuleViolation(
                    "changing a user's role requires its replacement profile."
                )

        updated = build_account(
            name=input_dto.name if input_dto.name is not None else current.name,
            email=input_dto.email if input_dto.email is not None else current.email,
            password_hash=(
                input_dto.password_hash
                if input_dto.password_hash is not None
                else current.password_hash
            ),
            role=role,
            user=current,
        )
        if input_dto.active is not None:
            updated.active = input_dto.active
        profile = build_profile(updated, input_dto.trainer, input_dto.client)
        saved = await self._users.update(updated, profile)
        profile = attach_profile_id(profile, saved)
        if profile is None and saved.id_user is not None:
            profile = await self._users.get_profile(saved.id_user)
        return UserOutputDTO.from_entity(saved, profile)
