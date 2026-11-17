"""Unit tests for client session registration and consultation."""

from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date, time

from app.application.dto.actor import ActorDTO
from app.application.dto.training_session_dto import RegisterTrainingSessionInputDTO
from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.application.use_cases.list_training_sessions import (
    ListTrainingSessionsUseCase,
)
from app.application.use_cases.register_training_session import (
    RegisterTrainingSessionUseCase,
)
from app.domain.entities.assignment import Assignment
from app.domain.entities.training_session import TrainingSession
from app.domain.value_objects.user_role import UserRole


class MemoryAssignments:
    def __init__(self, assignment: Assignment | None) -> None:
        self.assignment = assignment

    async def get_by_id(self, id_assignment: int) -> Assignment | None:
        if self.assignment and self.assignment.id_assignment == id_assignment:
            return self.assignment
        return None


class MemorySessions:
    def __init__(self) -> None:
        self.rows: list[TrainingSession] = []

    async def save(self, session: TrainingSession) -> TrainingSession:
        if any(
            row.id_assignment == session.id_assignment
            and row.session_date == session.session_date
            for row in self.rows
        ):
            raise DuplicateResource("session", "duplicate assignment/date")
        saved = replace(session, id_session=len(self.rows) + 1)
        self.rows.append(saved)
        return saved

    async def find_by_assignment_and_date(
        self, id_assignment: int, session_date: date
    ) -> TrainingSession | None:
        return next(
            (
                row
                for row in self.rows
                if row.id_assignment == id_assignment
                and row.session_date == session_date
            ),
            None,
        )

    async def list_by_assignment(self, id_assignment: int) -> list[TrainingSession]:
        return [row for row in self.rows if row.id_assignment == id_assignment]


def _assignment(client_id: int = 22) -> Assignment:
    return Assignment(
        id_assignment=5,
        id_routine=9,
        id_client=client_id,
        assignment_date=date(2026, 4, 1),
    )


def _request(**overrides) -> RegisterTrainingSessionInputDTO:
    values = {
        "actor": ActorDTO(id_user=22, role=UserRole.CLIENT),
        "id_assignment": 5,
        "session_date": date(2026, 4, 3),
        "start_time": time(9, 0),
        "end_time": time(10, 0),
        "intensity_perceived": 7,
        "completed": True,
        "observations": "Felt good",
    }
    values.update(overrides)
    return RegisterTrainingSessionInputDTO(**values)


class TrainingSessionUseCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_register_persists_all_session_attributes(self) -> None:
        sessions = MemorySessions()
        use_case = RegisterTrainingSessionUseCase(
            MemoryAssignments(_assignment()), sessions
        )

        result = await use_case.execute(_request())

        self.assertEqual(result.id_session, 1)
        self.assertEqual(result.id_assignment, 5)
        self.assertEqual(result.session_date, date(2026, 4, 3))
        self.assertEqual(result.start_time, time(9, 0))
        self.assertEqual(result.end_time, time(10, 0))
        self.assertEqual(result.intensity_perceived, 7)
        self.assertTrue(result.completed)
        self.assertEqual(result.observations, "Felt good")

    async def test_client_cannot_register_or_consult_another_clients_assignment(
        self,
    ) -> None:
        assignments = MemoryAssignments(_assignment(client_id=99))
        sessions = MemorySessions()
        register = RegisterTrainingSessionUseCase(assignments, sessions)
        consult = ListTrainingSessionsUseCase(assignments, sessions)

        with self.assertRaises(PermissionDenied):
            await register.execute(_request())
        with self.assertRaises(PermissionDenied):
            await consult.execute(_request().actor, 5)
        self.assertEqual(sessions.rows, [])

    async def test_missing_assignment_is_rejected(self) -> None:
        use_case = RegisterTrainingSessionUseCase(
            MemoryAssignments(None), MemorySessions()
        )

        with self.assertRaises(ResourceNotFound):
            await use_case.execute(_request())

    async def test_duplicate_assignment_date_is_rejected(self) -> None:
        sessions = MemorySessions()
        use_case = RegisterTrainingSessionUseCase(
            MemoryAssignments(_assignment()), sessions
        )
        await use_case.execute(_request())

        with self.assertRaises(DuplicateResource):
            await use_case.execute(_request())

    async def test_date_before_assignment_is_rejected(self) -> None:
        use_case = RegisterTrainingSessionUseCase(
            MemoryAssignments(_assignment()), MemorySessions()
        )

        with self.assertRaises(InvalidInput):
            await use_case.execute(_request(session_date=date(2026, 3, 31)))

    async def test_end_time_before_start_time_is_rejected(self) -> None:
        use_case = RegisterTrainingSessionUseCase(
            MemoryAssignments(_assignment()), MemorySessions()
        )

        with self.assertRaises(InvalidInput):
            await use_case.execute(
                _request(start_time=time(10, 0), end_time=time(9, 0))
            )

    async def test_client_can_consult_own_sessions(self) -> None:
        sessions = MemorySessions()
        register = RegisterTrainingSessionUseCase(
            MemoryAssignments(_assignment()), sessions
        )
        await register.execute(_request())
        consult = ListTrainingSessionsUseCase(
            MemoryAssignments(_assignment()), sessions
        )

        result = await consult.execute(_request().actor, 5)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].observations, "Felt good")


if __name__ == "__main__":
    unittest.main()
