"""Use case: authenticate a user with email and password (E4-01)."""

from __future__ import annotations

from app.application.dto.auth_dto import IssuedSessionDTO, LoginInputDTO
from app.application.exceptions import AuthenticationFailed
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.token_service import TokenService
from app.application.services.user_session_service import UserSessionService
from app.domain.repositories.user_repository import UserRepository


class AuthenticateUserUseCase:
    """Validate credentials, reload persisted state, and issue an access token.

    The token only carries the user identifier. Role and capabilities are
    always reconstructed from PostgreSQL so changes and deactivations apply to
    the next request without waiting for the token to expire.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        session_service: UserSessionService,
    ) -> None:
        self._users = user_repository
        self._passwords = password_hasher
        self._tokens = token_service
        self._sessions = session_service

    async def execute(self, input_dto: LoginInputDTO) -> IssuedSessionDTO:
        user = await self._users.get_by_email(input_dto.email.strip().lower())
        if user is None:
            raise AuthenticationFailed()

        if not self._passwords.verify(input_dto.password, user.password_hash):
            raise AuthenticationFailed()

        if not user.active:
            raise AuthenticationFailed("The account is inactive.")

        session = await self._sessions.build(user)
        issued = self._tokens.issue(session.id_user)
        return IssuedSessionDTO(
            access_token=issued.token,
            token_type="bearer",
            expires_at=issued.expires_at,
            user=session,
        )
