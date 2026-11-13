"""Use case: resolve the authenticated user behind a bearer token (E4-01)."""

from __future__ import annotations

from app.application.dto.auth_dto import UserSessionDTO
from app.application.exceptions import InvalidToken
from app.application.ports.token_service import TokenService
from app.application.services.user_session_service import UserSessionService
from app.domain.repositories.user_repository import UserRepository


class ResolveSessionUseCase:
    """Validate a token and reload the user's current role and capabilities."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_service: TokenService,
        session_service: UserSessionService,
    ) -> None:
        self._users = user_repository
        self._tokens = token_service
        self._sessions = session_service

    async def execute(self, token: str) -> UserSessionDTO:
        payload = self._tokens.decode(token)
        user = await self._users.get_by_id(payload.id_user)
        if user is None or not user.active:
            raise InvalidToken(
                "The access token does not identify an active user."
            )
        return await self._sessions.build(user)
