"""Small in-memory security adapters for application unit tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.application.exceptions import ExpiredToken, InvalidToken
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.token_service import IssuedToken, TokenPayload, TokenService


class FakePasswordHasher(PasswordHasher):
    """Reversible test double; never use this outside tests."""

    def hash(self, password: str) -> str:
        return f"fake:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"fake:{password}"


class FakeTokenService(TokenService):
    """Deterministic token service with explicit invalid/expired tokens."""

    def __init__(self, expire_minutes: int = 30) -> None:
        self._expire_minutes = expire_minutes

    def issue(self, id_user: int) -> IssuedToken:
        return IssuedToken(
            token=f"token:{id_user}",
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=self._expire_minutes),
        )

    def decode(self, token: str) -> TokenPayload:
        if token == "expired":
            raise ExpiredToken()
        if not token.startswith("token:"):
            raise InvalidToken()
        try:
            id_user = int(token.split(":", 1)[1])
        except (IndexError, ValueError) as error:
            raise InvalidToken() from error
        if id_user <= 0:
            raise InvalidToken()
        return TokenPayload(
            id_user=id_user,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=self._expire_minutes),
        )
