"""bcrypt password hashing adapter."""

from __future__ import annotations

from passlib.context import CryptContext

from app.application.ports.password_hasher import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """Hash and verify passwords with bcrypt via passlib."""

    def __init__(self, rounds: int = 12) -> None:
        if rounds < 10:
            raise ValueError("bcrypt rounds must be at least 10")
        self._context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=rounds,
        )

    def hash(self, password: str) -> str:
        return self._context.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._context.verify(password, password_hash)
        except (TypeError, ValueError):
            # Unknown algorithms or malformed stored hashes are treated as a
            # failed verification; they must never crash the login endpoint.
            return False
