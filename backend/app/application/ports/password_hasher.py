"""Password hashing port.

The application layer only knows that passwords can be hashed and verified. The
concrete algorithm and its parameters belong to infrastructure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Hash and verify user passwords without exposing the algorithm."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Return a one-way hash suitable for storing in ``app_user``."""

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        """Return whether ``password`` matches the stored hash."""
