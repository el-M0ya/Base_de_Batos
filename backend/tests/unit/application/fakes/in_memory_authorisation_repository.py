"""In-memory authorisation repository for authentication unit tests."""

from __future__ import annotations

from datetime import date
from typing import Optional

from app.application.exceptions import DuplicateResource
from app.domain.entities.authorisation import Authorisation
from app.domain.repositories.authorisation_repository import AuthorisationRepository


class InMemoryAuthorisationRepository(AuthorisationRepository):
    """Dictionary-backed trainer-program authorisation store."""

    def __init__(self, rows: Optional[list[Authorisation]] = None) -> None:
        self._rows: dict[tuple[int, int], Authorisation] = {
            (row.id_trainer, row.id_workout_program): row for row in rows or []
        }

    async def create(self, authorisation: Authorisation) -> Authorisation:
        key = (authorisation.id_trainer, authorisation.id_workout_program)
        if key in self._rows:
            raise DuplicateResource("authorisation", "already exists")
        self._rows[key] = authorisation
        return authorisation

    async def get(
        self, id_trainer: int, id_workout_program: int
    ) -> Optional[Authorisation]:
        return self._rows.get((id_trainer, id_workout_program))

    async def list(
        self,
        id_trainer: Optional[int] = None,
        id_workout_program: Optional[int] = None,
    ) -> list[Authorisation]:
        return [
            row
            for (trainer, program), row in self._rows.items()
            if (id_trainer is None or trainer == id_trainer)
            and (id_workout_program is None or program == id_workout_program)
        ]

    async def update(self, authorisation: Authorisation) -> Optional[Authorisation]:
        key = (authorisation.id_trainer, authorisation.id_workout_program)
        if key not in self._rows:
            return None
        self._rows[key] = authorisation
        return authorisation

    async def delete(self, id_trainer: int, id_workout_program: int) -> bool:
        return self._rows.pop((id_trainer, id_workout_program), None) is not None

    async def allows(
        self,
        id_trainer: int,
        id_workout_program: int,
        operation: str,
        on_date: date,
    ) -> bool:
        authorisation = await self.get(id_trainer, id_workout_program)
        if authorisation is None:
            return False
        if operation == "generate":
            return authorisation.allows_generation_on(on_date)
        if operation == "validate":
            return authorisation.allows_validation_on(on_date)
        return False
