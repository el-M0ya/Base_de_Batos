"""In-memory ``RoutineRepository`` for routine review unit tests.

The fake mirrors the parts of the SQL adapter that the review use cases need:
complete routine retrieval and validation persistence. Saving a validation
also updates the stored routine status, mimicking the E1-08 trigger so the
tests can assert that the application result and the persisted state agree.
"""

from __future__ import annotations

import copy
from typing import Optional

from app.application.exceptions import ResourceNotFound
from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.entities.routine_structure import RoutineStructure
from app.domain.entities.routine_validation import RoutineValidation
from app.domain.repositories.routine_repository import RoutineRepository


class InMemoryRoutineRepository(RoutineRepository):
    """Dictionary-backed routine and validation store."""

    def __init__(
        self,
        routines: Optional[list[tuple[Routine, RoutineStructure]]] = None,
    ) -> None:
        self._routines: dict[int, Routine] = {}
        self._structures: dict[int, RoutineStructure] = {}
        self._validations: list[RoutineValidation] = []
        self._next_routine_id = 1
        self._next_validation_id = 1

        for routine, structure in routines or []:
            self._store(routine, structure)

    def _store(
        self, routine: Routine, structure: RoutineStructure
    ) -> Routine:
        """Store copies and assign an identifier when the routine is new."""
        stored = copy.deepcopy(routine)
        if stored.id_routine is None:
            stored.id_routine = self._next_routine_id
        self._next_routine_id = max(
            self._next_routine_id, stored.id_routine + 1
        )
        self._routines[stored.id_routine] = stored
        self._structures[stored.id_routine] = copy.deepcopy(structure)
        return copy.deepcopy(stored)

    async def save(
        self, routine: Routine, structure: RoutineStructure
    ) -> Routine:
        """Persist a routine and its structure."""
        return self._store(routine, structure)

    async def get_complete(
        self, id_routine: int
    ) -> Optional[tuple[Routine, RoutineStructure]]:
        """Return copies of the routine and its structure, or ``None``."""
        routine = self._routines.get(id_routine)
        structure = self._structures.get(id_routine)
        if routine is None or structure is None:
            return None
        return copy.deepcopy(routine), copy.deepcopy(structure)

    async def list_by_program(self, id_workout_program: int) -> list[Routine]:
        """Return routines belonging to a workout program."""
        return [
            copy.deepcopy(routine)
            for routine in self._routines.values()
            if routine.id_workout_program == id_workout_program
        ]

    async def save_validation(
        self, validation: RoutineValidation
    ) -> RoutineValidation:
        """Store a validation and synchronise the routine status like E1-08."""
        routine = self._routines.get(validation.id_routine)
        if routine is None:
            raise ResourceNotFound("routine", validation.id_routine)

        saved = copy.deepcopy(validation)
        if saved.id_validation is None:
            saved.id_validation = self._next_validation_id
        self._next_validation_id = max(
            self._next_validation_id, saved.id_validation + 1
        )

        self._validations.append(saved)

        # The database trigger copies the decision into routine.status. Mirror
        # it here so the fake returns the same observable state as PostgreSQL.
        routine.status = RoutineStatus(saved.decision.value)
        return copy.deepcopy(saved)

    async def list_validations(self, id_routine: int) -> list[RoutineValidation]:
        """Return the routine history in reverse chronological order."""
        validations = [
            copy.deepcopy(validation)
            for validation in self._validations
            if validation.id_routine == id_routine
        ]
        return sorted(
            validations,
            key=lambda validation: (
                validation.validation_date,
                validation.id_validation or 0,
            ),
            reverse=True,
        )
