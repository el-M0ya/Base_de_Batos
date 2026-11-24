"""Unit tests for assigning a routine to a client."""

from __future__ import annotations

import pathlib
import sys
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from app.application.dto.routine_assignment_dto import AssignRoutineInputDTO
from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.application.use_cases.assign_routine import AssignRoutineUseCase
from app.domain.entities.enrolment import Enrolment
from app.domain.entities.routine import Routine
from app.domain.entities.routine_structure import RoutineStructure
from fakes.in_memory_assignment_repository import InMemoryAssignmentRepository
from fakes.in_memory_enrolment_repository import InMemoryEnrolmentRepository
from fakes.in_memory_routine_repository import InMemoryRoutineRepository


ROUTINE_ID = 201
CLIENT_ID = 301
PROGRAM_ID = 401
START_DATE = date(2026, 2, 1)
END_DATE = date(2026, 4, 30)


class AssignRoutineUseCaseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        routine = Routine(
            id_routine=ROUTINE_ID,
            id_workout_program=PROGRAM_ID,
            id_trainer_creator=501,
        )
        self.routines = InMemoryRoutineRepository(
            [(routine, RoutineStructure(id_routine=ROUTINE_ID))]
        )
        self.enrolments = InMemoryEnrolmentRepository(
            clients={CLIENT_ID}, programs={PROGRAM_ID}
        )
        self.enrolments.enrolments.append(
            Enrolment(
                id_client=CLIENT_ID,
                id_workout_program=PROGRAM_ID,
                enrollment_date=date(2026, 1, 15),
            )
        )
        self.assignments = InMemoryAssignmentRepository()
        self.use_case = AssignRoutineUseCase(
            self.routines, self.enrolments, self.assignments
        )

    def _input(self, **overrides) -> AssignRoutineInputDTO:
        values = {
            "id_routine": ROUTINE_ID,
            "id_client": CLIENT_ID,
            "assignment_date": START_DATE,
            "end_date": END_DATE,
        }
        values.update(overrides)
        return AssignRoutineInputDTO(**values)

    async def test_assigns_routine_and_preserves_dates(self) -> None:
        result = await self.use_case.execute(self._input())

        self.assertEqual(1, result.id_assignment)
        self.assertEqual(ROUTINE_ID, result.id_routine)
        self.assertEqual(CLIENT_ID, result.id_client)
        self.assertEqual(START_DATE, result.assignment_date)
        self.assertEqual(END_DATE, result.end_date)
        self.assertEqual(1, self.assignments.save_calls)

    async def test_allows_assignment_without_end_date(self) -> None:
        result = await self.use_case.execute(self._input(end_date=None))

        self.assertIsNone(result.end_date)
        self.assertEqual(START_DATE, result.assignment_date)

    async def test_rejects_missing_routine(self) -> None:
        self.routines = InMemoryRoutineRepository([])
        use_case = AssignRoutineUseCase(
            self.routines, self.enrolments, self.assignments
        )

        with self.assertRaises(ResourceNotFound) as raised:
            await use_case.execute(self._input())

        self.assertEqual("routine", raised.exception.resource)
        self.assertEqual(0, self.assignments.save_calls)

    async def test_rejects_missing_client(self) -> None:
        self.enrolments = InMemoryEnrolmentRepository(
            clients={999}, programs={PROGRAM_ID}
        )
        use_case = AssignRoutineUseCase(
            self.routines, self.enrolments, self.assignments
        )

        with self.assertRaises(ResourceNotFound) as raised:
            await use_case.execute(self._input())

        self.assertEqual("client", raised.exception.resource)
        self.assertEqual(0, self.assignments.save_calls)

    async def test_rejects_client_not_enrolled_in_routine_program(self) -> None:
        self.enrolments.enrolments.clear()

        with self.assertRaises(BusinessRuleViolation):
            await self.use_case.execute(self._input())

        self.assertEqual(0, self.assignments.save_calls)

    async def test_rejects_duplicate_assignment(self) -> None:
        await self.use_case.execute(self._input())

        with self.assertRaises(DuplicateResource) as raised:
            await self.use_case.execute(self._input())

        self.assertEqual("assignment", raised.exception.resource)
        self.assertEqual(1, self.assignments.save_calls)
        self.assertEqual(1, len(self.assignments.assignments))

    async def test_rejects_end_date_before_start_date(self) -> None:
        with self.assertRaises(InvalidInput):
            await self.use_case.execute(
                self._input(end_date=date(2026, 1, 31))
            )

        self.assertEqual(0, self.assignments.save_calls)

    async def test_propagates_application_integrity_error(self) -> None:
        integrity_error = DuplicateResource(
            "assignment", "database unique violation"
        )
        self.assignments.fail_on_save = integrity_error

        with self.assertRaises(DuplicateResource) as raised:
            await self.use_case.execute(self._input())

        self.assertIs(integrity_error, raised.exception)


if __name__ == "__main__":
    unittest.main()
