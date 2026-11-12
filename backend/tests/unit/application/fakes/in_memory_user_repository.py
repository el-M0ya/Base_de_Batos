"""In-memory user repository for application-layer tests."""

from __future__ import annotations

from datetime import datetime

from app.domain.entities.client import Client
from app.domain.entities.trainer import Trainer
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    """Store users and profiles without external infrastructure."""

    def __init__(self) -> None:
        self._users: dict[int, User] = {}
        self._profiles: dict[int, Trainer | Client] = {}
        self._next_id = 1

    async def get_by_id(self, id_user: int) -> User | None:
        return self._users.get(id_user)

    async def get_by_email(self, email: str) -> User | None:
        return next(
            (user for user in self._users.values() if user.email == email),
            None,
        )

    async def list_users(self) -> tuple[User, ...]:
        return tuple(self._users[id_user] for id_user in sorted(self._users))

    async def get_profile(self, id_user: int) -> Trainer | Client | None:
        return self._profiles.get(id_user)

    async def save(
        self,
        user: User,
        profile: Trainer | Client | None = None,
    ) -> User:
        user.id_user = self._next_id
        self._next_id += 1
        user.created_at = datetime(2026, 1, 1)
        self._users[user.id_user] = user
        self._save_profile(user, profile)
        return user

    async def update(
        self,
        user: User,
        profile: Trainer | Client | None = None,
    ) -> User:
        if user.id_user is None:
            raise AssertionError("The test repository requires a persisted user.")
        self._users[user.id_user] = user
        if profile is not None:
            self._save_profile(user, profile)
        return user

    async def deactivate(self, id_user: int) -> User:
        user = self._users[id_user]
        user.active = False
        return user

    def _save_profile(
        self,
        user: User,
        profile: Trainer | Client | None,
    ) -> None:
        if profile is None or user.id_user is None:
            return
        if isinstance(profile, Trainer):
            profile.id_trainer = user.id_user
        else:
            profile.id_client = user.id_user
        self._profiles[user.id_user] = profile
