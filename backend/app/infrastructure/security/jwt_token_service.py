"""JWT access-token adapter using python-jose."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt

from app.application.exceptions import ExpiredToken, InvalidToken
from app.application.ports.token_service import IssuedToken, TokenPayload, TokenService


class JwtTokenService(TokenService):
    """Issue and validate signed, expiring JWT access tokens."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        expire_minutes: int = 30,
    ) -> None:
        if len(secret_key) < 32:
            raise ValueError("JWT secret key must contain at least 32 characters")
        if expire_minutes < 1:
            raise ValueError("JWT expiry must be at least one minute")
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    def issue(self, id_user: int) -> IssuedToken:
        if not isinstance(id_user, int) or isinstance(id_user, bool) or id_user <= 0:
            raise ValueError("id_user must be a positive integer")

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._expire_minutes)
        token = jwt.encode(
            {
                "sub": str(id_user),
                "iat": now,
                "exp": expires_at,
            },
            self._secret_key,
            algorithm=self._algorithm,
        )
        return IssuedToken(token=token, expires_at=expires_at)

    def decode(self, token: str) -> TokenPayload:
        try:
            claims = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"require_exp": True, "require_sub": True},
            )
        except ExpiredSignatureError as error:
            raise ExpiredToken() from error
        except JWTError as error:
            raise InvalidToken() from error

        try:
            id_user = int(claims["sub"])
            expires_at = datetime.fromtimestamp(int(claims["exp"]), tz=timezone.utc)
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise InvalidToken("The access token has invalid claims.") from error

        if id_user <= 0:
            raise InvalidToken("The access token has invalid claims.")
        return TokenPayload(id_user=id_user, expires_at=expires_at)
