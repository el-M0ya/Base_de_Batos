"""In-memory assignment repository for application use-case tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Optional

from app.application.exceptions import DuplicateResource
from app.domain.entities.assignment import Assignment
from app.domain.repositories.assignment_repository import AssignmentRepository


class InMemoryAssignmentRepository(AssignmentRepository):
    """Dictionary-backed assignment store with a configurable save failure."""

    def __init__(self) -> None:
        self.assignments: dict[int, Assignment] = {}
        self.save_calls = 0
        self.fail_on_save: Optional[Exception] = None
        self._next_id = 1

    async def find_by_routine_and_client(
        self, id_routine: int, id_client: int
    ) -> Optional[Assignment]:
        return next(
            (
                assignment
                for assignment in self.assignments.values()
                if assignment.id_routine == id_routine
                and assignment.id_client == id_client
            ),
            None,
        )

    async def list_active_for_client(
        self, id_client: int, on_date: Optional[date] = None
    ) -> list[Assignment]:
        return [
            assignment
            for assignment in self.assignments.values()
            if assignment.id_client == id_client and assignment.is_active(on_date)
        ]

    async def save(self, assignment: Assignment) -> Assignment:
        self.save_calls += 1
        if self.fail_on_save is not None:
            raise self.fail_on_save

        if await self.find_by_routine_and_client(
            assignment.id_routine, assignment.id_client
        ):
            raise DuplicateResource(
                "assignment",
                "the routine has already been assigned to this client",
            )

        saved = replace(assignment, id_assignment=self._next_id)
        self._next_id += 1
        self.assignments[saved.id_assignment] = saved
        return saved
