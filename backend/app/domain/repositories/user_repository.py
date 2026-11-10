"""Domain contract for user persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.user import User


class UserRepository(ABC):
    """Persistence operations for user accounts."""

    @abstractmethod
    async def get_by_id(self, id_user: int) -> Optional[User]:
        """Return a user by identifier, or ``None`` when it does not exist."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Return a user by email, or ``None`` when it does not exist."""

    @abstractmethod
    async def save(self, user: User) -> User:
        """Persist a user and return it with its assigned identifier."""
