"""Unit tests for report query parameterization and result mapping."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from app.application.dto.informational_report_dto import (
    ExerciseUsageByProgramQuery,
    RoutinesByProgramQuery,
    ValidationsByReviewerQuery,
)
from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.infrastructure.persistence.queries.informational_reports_sql import (
    InformationalReportsSql,
)


class FakeCursor:
    def __init__(self, rows) -> None:
        self._rows = rows

    async def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self, *responses) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, tuple]] = []

    async def execute(self, sql, params):
        self.calls.append((sql, params))
        return FakeCursor(self._responses.pop(0))


class FakeTransactionManager:
    def __init__(self, connection) -> None:
        self._connection = connection

    def connection(self):
        return self._connection


class InformationalReportQueryTests(unittest.IsolatedAsyncioTestCase):
    async def test_rep01_maps_generation_snapshot_and_binds_filters(self) -> None:
        connection = FakeConnection(
            [
                {
                    "id_routine": 20,
                    "status": "APPROVED",
                    "id_trainer_creator": 7,
                    "trainer_name": "Trainer",
                    "creation_date": date(2026, 4, 5),
                    "total_exercises": 8,
                    "intensity_level": "alto",
                    "cardio_ratio": Decimal("10.00"),
                    "strength_ratio": Decimal("80.00"),
                    "flexibility_ratio": Decimal("10.00"),
                    "covered_muscle_group_ids": [2, 3],
                }
            ]
        )
        queries = InformationalReportsSql(FakeTransactionManager(connection))

        rows = await queries.routines_by_program(
            RoutinesByProgramQuery(11, date(2026, 4, 1), date(2026, 4, 30))
        )

        self.assertEqual(rows[0].trainer_name, "Trainer")
        self.assertEqual(rows[0].strength_ratio, Decimal("80.00"))
        self.assertEqual(rows[0].covered_muscle_group_ids, (2, 3))
        self.assertEqual(
            connection.calls[0][1],
            (
                11,
                date(2026, 4, 1),
                date(2026, 4, 1),
                date(2026, 4, 30),
                date(2026, 4, 30),
            ),
        )

    async def test_rep02_returns_grouped_usage_without_user_sql(self) -> None:
        connection = FakeConnection(
            [
                {
                    "id_exercise": 4,
                    "exercise_name": "Squat",
                    "routine_intensity": "alto",
                    "id_muscle_group": 3,
                    "muscle_group_name": "Legs",
                    "usage_count": 12,
                }
            ]
        )
        queries = InformationalReportsSql(FakeTransactionManager(connection))

        rows = await queries.exercise_usage_by_program(
            ExerciseUsageByProgramQuery(11)
        )

        self.assertEqual(rows[0].usage_count, 12)
        sql, params = connection.calls[0]
        self.assertIn("r.status = 'APPROVED'", sql)
        self.assertEqual(params, (11, None, None, None, None))

    async def test_rep03_maps_each_review_event_and_binds_reviewer(self) -> None:
        connection = FakeConnection(
            [
                {
                    "id_validation": 9,
                    "id_routine": 20,
                    "id_reviewer": 8,
                    "reviewer_name": "Room Chief",
                    "validation_date": date(2026, 4, 9),
                    "decision": "REJECTED",
                    "observations": "Lower the volume",
                }
            ]
        )
        queries = InformationalReportsSql(FakeTransactionManager(connection))

        rows = await queries.validations_by_reviewer(
            ValidationsByReviewerQuery(8, date(2026, 4, 1), date(2026, 4, 30))
        )

        self.assertEqual(rows[0].observations, "Lower the volume")
        self.assertEqual(connection.calls[0][1][0], 8)

    def test_reversed_date_range_is_rejected(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            RoutinesByProgramQuery(11, date(2026, 5, 1), date(2026, 4, 1))


if __name__ == "__main__":
    unittest.main()
