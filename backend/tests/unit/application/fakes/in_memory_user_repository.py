"""In-memory user repository for authentication unit tests."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from app.application.exceptions import DuplicateResource
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    """Dictionary-backed user store with the same lookup rules as SQL."""

    def __init__(self, users: Optional[list[User]] = None) -> None:
        self._rows: dict[int, User] = {}
        self._next_id = 1
        for user in users or []:
            self.save_sync(user)

    def save_sync(self, user: User) -> User:
        if user.id_user is None:
            saved = replace(user, id_user=self._next_id)
            self._next_id += 1
        else:
            saved = user
        for identifier, existing in self._rows.items():
            if (
                existing.email.lower() == saved.email.lower()
                and identifier != saved.id_user
            ):
                raise DuplicateResource("user", "email already exists")
        self._rows[saved.id_user] = saved  # type: ignore[index]
        return saved

    async def get_by_id(self, id_user: int) -> Optional[User]:
        return self._rows.get(id_user)

    async def get_by_email(self, email: str) -> Optional[User]:
        normalized = email.strip().lower()
        for user in self._rows.values():
            if user.email.lower() == normalized:
                return user
        return None

    async def save(self, user: User) -> User:
        return self.save_sync(user)
