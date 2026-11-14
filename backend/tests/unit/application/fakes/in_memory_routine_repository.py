"""In-memory implementation of ``RoutineRepository`` for unit tests."""

from __future__ import annotations

from typing import Optional

from app.application.exceptions import BusinessRuleViolation
from app.domain.entities.routine import Routine
from app.domain.entities.routine_structure import RoutineStructure
from app.domain.entities.routine_validation import RoutineValidation
from app.domain.repositories.routine_repository import RoutineRepository


class InMemoryRoutineRepository(RoutineRepository):
    """Dictionary-backed routine store with an optional save failure."""

    def __init__(self) -> None:
        self.routines: dict[int, Routine] = {}
        self.structures: dict[int, RoutineStructure] = {}
        self.saved: list[tuple[Routine, RoutineStructure]] = []
        self.fail_on_save = False
        self._next_id = 1

    async def save(
        self, routine: Routine, structure: RoutineStructure
    ) -> Routine:
        """Store the aggregate or raise when the test enabled a failure."""
        if self.fail_on_save:
            raise BusinessRuleViolation("forced routine persistence failure")
        if getattr(routine, "_parameters", None) is None:
            raise ValueError("routine is missing generation parameters")
        if not getattr(routine, "_contains", None):
            raise ValueError("routine is missing its exercise composition")

        routine.id_routine = self._next_id
        self._next_id += 1
        self.routines[routine.id_routine] = routine
        self.structures[routine.id_routine] = structure
        self.saved.append((routine, structure))
        return routine

    async def get_complete(
        self, id_routine: int
    ) -> Optional[tuple[Routine, RoutineStructure]]:
        """Return the stored aggregate, if present."""
        routine = self.routines.get(id_routine)
        if routine is None:
            return None
        return routine, self.structures[id_routine]

    async def list_by_program(self, id_workout_program: int) -> list[Routine]:
        """Return routines ordered by identifier."""
        return sorted(
            (
                routine
                for routine in self.routines.values()
                if routine.id_workout_program == id_workout_program
            ),
            key=lambda routine: routine.id_routine or 0,
        )

    async def save_validation(
        self, validation: RoutineValidation
    ) -> RoutineValidation:
        """Validation history is outside the scope of these unit tests."""
        raise NotImplementedError

    async def list_validations(self, id_routine: int) -> list[RoutineValidation]:
        """Validation history is outside the scope of these unit tests."""
        return []
