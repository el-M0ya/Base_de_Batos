"""Domain contract for user persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.client import Client
from app.domain.entities.trainer import Trainer
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
    async def list_users(self) -> tuple[User, ...]:
        """Return all user accounts, including their active status."""

    @abstractmethod
    async def get_profile(self, id_user: int) -> Trainer | Client | None:
        """Return the specialization profile associated with a user."""

    @abstractmethod
    async def save(
        self,
        user: User,
        profile: Trainer | Client | None = None,
    ) -> User:
        """Persist a user and its optional specialization profile atomically."""

    @abstractmethod
    async def update(
        self,
        user: User,
        profile: Trainer | Client | None = None,
    ) -> User:
        """Update a user and its optional specialization profile atomically."""

    @abstractmethod
    async def deactivate(self, id_user: int) -> User:
        """Deactivate a user without deleting its historical records."""
