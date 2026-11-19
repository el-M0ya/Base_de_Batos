"""In-memory implementation of ``RoutineRepository`` for unit tests."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from app.application.exceptions import BusinessRuleViolation, DuplicateResource
from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.entities.routine_structure import RoutineStructure
from app.domain.entities.routine_validation import RoutineValidation
from app.domain.repositories.routine_repository import RoutineRepository


class InMemoryRoutineRepository(RoutineRepository):
    """Dictionary-backed routine store with an optional save failure."""

    def __init__(
        self,
        seed: list[tuple[Routine, RoutineStructure]] | None = None,
    ) -> None:
        self.routines: dict[int, Routine] = {}
        self.structures: dict[int, RoutineStructure] = {}
        self.validations: dict[int, list[RoutineValidation]] = {}
        self.saved: list[tuple[Routine, RoutineStructure]] = []
        self.fail_on_save = False
        self.fail_on_mark_replaced = False
        self._next_id = 1
        for routine, structure in seed or []:
            if routine.id_routine is None:
                raise ValueError("seed routines must have a persisted identifier")
            self.routines[routine.id_routine] = routine
            self.structures[routine.id_routine] = structure
            self._next_id = max(self._next_id, routine.id_routine + 1)

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
        if routine.id_routine_origin is not None and any(
            item.id_routine_origin == routine.id_routine_origin
            for item in self.routines.values()
        ):
            raise DuplicateResource("routine successor", "source already has a successor")

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
        return replace(routine), self.structures[id_routine]

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
        """Store validation history and mirror the database status trigger."""
        if validation.id_routine not in self.routines:
            raise BusinessRuleViolation("routine not found")
        rows = self.validations.setdefault(validation.id_routine, [])
        saved = replace(validation, id_validation=len(rows) + 1)
        rows.append(saved)
        routine = replace(self.routines[validation.id_routine])
        routine.status = (
            RoutineStatus.APPROVED
            if saved.is_approval()
            else RoutineStatus.REJECTED
        )
        self.routines[validation.id_routine] = routine
        return saved

    async def list_validations(self, id_routine: int) -> list[RoutineValidation]:
        """Return a copy of the routine's validation history."""
        rows = self.validations.get(id_routine, [])
        return [
            replace(row)
            for row in sorted(
                rows,
                key=lambda item: (item.validation_date, item.id_validation or 0),
                reverse=True,
            )
        ]

    async def mark_replaced(
        self, id_routine: int, expected_status: RoutineStatus
    ) -> Routine:
        """Mirror the conditional source update in the SQL repository."""
        if self.fail_on_mark_replaced:
            raise BusinessRuleViolation("forced source status update failure")
        source = self.routines.get(id_routine)
        if (
            source is None
            or source.status is not expected_status
            or not self.validations.get(id_routine)
            or not any(item.id_routine_origin == id_routine for item in self.routines.values())
        ):
            raise BusinessRuleViolation("routine replacement preconditions failed")
        replaced = replace(source, status=RoutineStatus.REPLACED)
        self.routines[id_routine] = replaced
        return replaced
