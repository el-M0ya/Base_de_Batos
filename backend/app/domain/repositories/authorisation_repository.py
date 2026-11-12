"""Persistence contract for trainer-to-program authorizations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.domain.entities.authorisation import Authorisation


class AuthorisationRepository(ABC):
    @abstractmethod
    async def create(self, authorisation: Authorisation) -> Authorisation: ...

    @abstractmethod
    async def get(self, id_trainer: int, id_workout_program: int) -> Authorisation | None: ...

    @abstractmethod
    async def list(self, id_trainer: int | None = None, id_workout_program: int | None = None) -> list[Authorisation]: ...

    @abstractmethod
    async def update(self, authorisation: Authorisation) -> Authorisation | None: ...

    @abstractmethod
    async def delete(self, id_trainer: int, id_workout_program: int) -> bool: ...

    async def allows(self, id_trainer: int, id_workout_program: int, operation: str, on_date: date) -> bool:
        authorization = await self.get(id_trainer, id_workout_program)
        if authorization is None:
            return False
        if operation == "generate":
            return authorization.allows_generation_on(on_date)
        if operation == "validate":
            return authorization.allows_validation_on(on_date)
        raise ValueError("operation must be 'generate' or 'validate'")
