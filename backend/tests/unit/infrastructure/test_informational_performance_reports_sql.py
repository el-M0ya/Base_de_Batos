"""Unit checks for REP-04 through REP-06 SQL behavior."""

from __future__ import annotations

import unittest

from app.application.dto.informational_performance_report_dto import (
    ProgramDistributionQuery,
    RoutinePerformanceQuery,
)
from app.infrastructure.persistence.queries.informational_performance_reports_sql import (
    InformationalPerformanceReportsSql,
)


class _Cursor:
    def __init__(self, rows):
        self.rows = rows

    async def fetchall(self):
        return self.rows


class _Connection:
    def __init__(self, rows=()):
        self.rows = rows
        self.calls = []

    async def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return _Cursor(self.rows)


class _Transaction:
    def __init__(self, connection):
        self._connection = connection

    def connection(self):
        return self._connection


class InformationalPerformanceReportsSqlTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_results_are_empty_tuples_and_routine_id_is_bound(self):
        connection = _Connection()
        reports = InformationalPerformanceReportsSql(_Transaction(connection))
        self.assertEqual(
            await reports.routine_performance(RoutinePerformanceQuery(12)), ()
        )
        self.assertEqual(connection.calls[0][1], (12,))

    async def test_no_abandonment_formula_is_reported_as_pending(self):
        reports = InformationalPerformanceReportsSql(_Transaction(_Connection()))
        result = await reports.exercise_abandonment_ranking()
        self.assertFalse(result.available)
        self.assertEqual(result.status, "DEFINITION_PENDING")
        self.assertEqual(result.rows, ())

    async def test_program_without_routines_can_be_returned(self):
        connection = _Connection(
            [
                {
                    "id_workout_program": 1,
                    "program_name": "Empty",
                    "id_muscle_group": None,
                    "muscle_group_name": None,
                    "intensity_level": None,
                    "exercise_count": 0,
                    "routine_count": 0,
                    "balance_criteria_met": None,
                    "balance_status": "CRITERIA_UNSPECIFIED",
                }
            ]
        )
        reports = InformationalPerformanceReportsSql(_Transaction(connection))
        rows = await reports.program_distributions(ProgramDistributionQuery())
        self.assertEqual(rows[0].routine_count, 0)
        self.assertIsNone(rows[0].balance_criteria_met)


if __name__ == "__main__":
    unittest.main()
