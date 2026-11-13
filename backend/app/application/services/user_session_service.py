"""Build the authenticated session shared by login and token resolution."""

from __future__ import annotations

from datetime import date

from app.application.dto.actor import CapabilitiesDTO
from app.application.dto.auth_dto import UserSessionDTO
from app.application.exceptions import InvalidInput
from app.domain.entities.user import User
from app.domain.repositories.authorisation_repository import AuthorisationRepository
from app.domain.value_objects.user_role import UserRole


class UserSessionService:
    """Derive role and capabilities from the persisted user and authorisations."""

    def __init__(self, authorisation_repository: AuthorisationRepository) -> None:
        self._authorisations = authorisation_repository

    async def build(
        self,
        user: User,
        on_date: date | None = None,
    ) -> UserSessionDTO:
        """Return the session for a persisted user.

        Capabilities are never trusted from the token: they are recomputed from
        active ``authorises`` rows on every call. This makes deactivations and
        permission changes take effect immediately.
        """
        if user.id_user is None:
            raise InvalidInput("the user must be persisted before starting a session")

        effective_date = on_date or date.today()
        capabilities = await self._capabilities(user, effective_date)
        return UserSessionDTO(
            id_user=user.id_user,
            email=user.email,
            role=user.role,
            capabilities=capabilities,
            active=user.active,
        )

    async def _capabilities(
        self,
        user: User,
        on_date: date,
    ) -> CapabilitiesDTO:
        if user.role is not UserRole.TRAINER:
            return CapabilitiesDTO()

        authorisations = await self._authorisations.list(id_trainer=user.id_user)
        active = [item for item in authorisations if item.is_active_on(on_date)]
        return CapabilitiesDTO(
            can_generate=any(item.can_generate for item in active),
            can_validate=any(item.can_validate for item in active),
        )
