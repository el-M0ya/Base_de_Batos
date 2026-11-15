"""Access-token port.

Application use cases issue and decode expiring access tokens through this
contract. JWT, signing keys, and library-specific exceptions stay in
infrastructure and are translated to application errors there.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IssuedToken:
    """A signed access token and its absolute expiration instant (UTC)."""

    token: str
    expires_at: datetime


@dataclass(frozen=True)
class TokenPayload:
    """Claims required by the application after successful token validation."""

    id_user: int
    expires_at: datetime


class TokenService(ABC):
    """Issue and validate expiring access tokens."""

    @abstractmethod
    def issue(self, id_user: int) -> IssuedToken:
        """Return a signed token for the user and its expiration instant."""

    @abstractmethod
    def decode(self, token: str) -> TokenPayload:
        """Validate a token and return its claims.

        Implementations must raise :class:`ExpiredToken` for expired tokens and
        :class:`InvalidToken` for any other invalid token.
        """
