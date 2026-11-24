"""Integration coverage for informational report queries REP-01 to REP-03."""

from __future__ import annotations

import asyncio
from datetime import date
from uuid import uuid4

import pytest

pytest.importorskip("psycopg")
pytest.importorskip("psycopg_pool")

import psycopg

from app.application.dto.informational_report_dto import (
    ExerciseUsageByProgramQuery,
    RoutinesByProgramQuery,
    ValidationsByReviewerQuery,
)
from app.infrastructure.persistence.queries.informational_reports_sql import (
    InformationalReportsSql,
)
from backend.tests.integration.base import IntegrationTestCase
from backend.tests.integration.support.database import (
    _target_db_dsn,
    get_test_pool,
)


class _BoundTransaction:
    def __init__(self, connection) -> None:
        self._connection = connection

    def connection(self):
        return self._connection


class InformationalReportsIntegrationTests(IntegrationTestCase):
    """Exercise query filters and mappings against the PostgreSQL test schema."""

    def _seed(self) -> dict[str, int]:
        suffix = uuid4().hex[:10]
        with psycopg.connect(_target_db_dsn(), autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO app_user (name, email, password_hash, role)
                       VALUES (%s, %s, 'test', 'TRAINER') RETURNING id_user""",
                    (f"Report Creator {suffix}", f"creator-{suffix}@example.test"),
                )
                creator_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO trainer (id_trainer, specialty) VALUES (%s, 'GENERAL')",
                    (creator_id,),
                )
                cursor.execute(
                    """INSERT INTO app_user (name, email, password_hash, role)
                       VALUES (%s, %s, 'test', 'TRAINER') RETURNING id_user""",
                    (f"Reviewer One {suffix}", f"reviewer1-{suffix}@example.test"),
                )
                reviewer_one = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO trainer (id_trainer, specialty) VALUES (%s, 'ROOM_CHIEF')",
                    (reviewer_one,),
                )
                cursor.execute(
                    """INSERT INTO app_user (name, email, password_hash, role)
                       VALUES (%s, %s, 'test', 'TRAINER') RETURNING id_user""",
                    (f"Reviewer Two {suffix}", f"reviewer2-{suffix}@example.test"),
                )
                reviewer_two = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO trainer (id_trainer, specialty) VALUES (%s, 'ROOM_CHIEF')",
                    (reviewer_two,),
                )
                cursor.execute(
                    """INSERT INTO workout_program (name, objective)
                       VALUES (%s, 'Informational report integration')
                       RETURNING id_workout_program""",
                    (f"Report Program {suffix}",),
                )
                program_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO muscle_group (name) VALUES (%s) RETURNING id_muscle_group",
                    (f"Report Muscle {suffix}",),
                )
                muscle_id = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT id_exercise_type FROM exercise_type WHERE name = 'fuerza'"
                )
                type_id = cursor.fetchone()[0]
                exercise_ids = []
                for name in ("Report Exercise A", "Report Exercise B"):
                    cursor.execute(
                        """INSERT INTO exercise
                               (name, registration_date, id_exercise_type,
                                id_muscle_group, id_trainer_creator)
                           VALUES (%s, DATE '2026-01-01', %s, %s, %s)
                           RETURNING id_exercise""",
                        (f"{name} {suffix}", type_id, muscle_id, creator_id),
                    )
                    exercise_ids.append(cursor.fetchone()[0])

                routine_ids = []
                routine_specs = (
                    (date(2026, 4, 2), "alto"),
                    (date(2026, 4, 5), "alto"),
                    (date(2026, 5, 12), "medio"),
                )
                for creation_date, intensity in routine_specs:
                    cursor.execute(
                        """INSERT INTO routine
                               (status, creation_date, id_workout_program,
                                id_trainer_creator)
                           VALUES ('PENDING_REVIEW', %s, %s, %s)
                           RETURNING id_routine""",
                        (creation_date, program_id, creator_id),
                    )
                    routine_id = cursor.fetchone()[0]
                    routine_ids.append(routine_id)
                    cursor.execute(
                        """INSERT INTO parameters_routine
                               (id_routine, total_exercises, intensity_level,
                                cardio_ratio, strength_ratio, flexibility_ratio,
                                covered_muscle_group_ids)
                           VALUES (%s, 4, %s, 0, 100, 0, %s)""",
                        (routine_id, intensity, [muscle_id]),
                    )

                for routine_id, exercise_id in (
                    (routine_ids[0], exercise_ids[0]),
                    (routine_ids[1], exercise_ids[0]),
                    (routine_ids[1], exercise_ids[1]),
                    (routine_ids[2], exercise_ids[1]),
                ):
                    cursor.execute(
                        """INSERT INTO contains
                               (id_routine, id_exercise, execution_order,
                                sets, repetitions, rest_time_seconds)
                           VALUES (%s, %s, 1, 3, 10, 60)""",
                        (routine_id, exercise_id),
                    )

                for routine_id, reviewer_id, review_date, decision, observations in (
                    (routine_ids[0], reviewer_one, date(2026, 4, 3), "APPROVED", None),
                    (routine_ids[1], reviewer_one, date(2026, 4, 10), "APPROVED", None),
                    (
                        routine_ids[2],
                        reviewer_two,
                        date(2026, 5, 13),
                        "REJECTED",
                        "Revise volume",
                    ),
                ):
                    cursor.execute(
                        """INSERT INTO validate
                               (id_routine, id_room_chief, fecha_validacion,
                                decision, observaciones)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (routine_id, reviewer_id, review_date, decision, observations),
                    )

        return {
            "program_id": program_id,
            "creator_id": creator_id,
            "muscle_id": muscle_id,
            "reviewer_one": reviewer_one,
            "reviewer_two": reviewer_two,
            "exercise_a": exercise_ids[0],
        }

    async def _query(self, method: str, filter_dto):
        pool = await get_test_pool()
        async with pool.connection() as connection:
            reports = InformationalReportsSql(_BoundTransaction(connection))
            return await getattr(reports, method)(filter_dto)

    def test_rep01_program_and_creation_date_filters(self) -> None:
        data = self._seed()
        rows = asyncio.run(
            self._query(
                "routines_by_program",
                RoutinesByProgramQuery(
                    data["program_id"], date(2026, 4, 1), date(2026, 4, 30)
                ),
            )
        )

        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0].trainer_name.startswith("Report Creator"))
        self.assertEqual(rows[0].id_trainer_creator, data["creator_id"])
        self.assertEqual(rows[0].total_exercises, 4)
        self.assertEqual(rows[0].covered_muscle_group_ids, (data["muscle_id"],))

    def test_rep02_counts_approved_routines_by_intensity_and_muscle(self) -> None:
        data = self._seed()
        rows = asyncio.run(
            self._query(
                "exercise_usage_by_program",
                ExerciseUsageByProgramQuery(
                    data["program_id"], date(2026, 4, 1), date(2026, 4, 30)
                ),
            )
        )

        self.assertEqual(len(rows), 2)
        exercise_a = next(row for row in rows if row.id_exercise == data["exercise_a"])
        self.assertEqual(exercise_a.usage_count, 2)
        self.assertEqual(exercise_a.routine_intensity, "alto")

    def test_rep03_filters_reviewer_and_validation_date(self) -> None:
        data = self._seed()
        rows = asyncio.run(
            self._query(
                "validations_by_reviewer",
                ValidationsByReviewerQuery(
                    data["reviewer_one"], date(2026, 4, 8), date(2026, 4, 30)
                ),
            )
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].validation_date, date(2026, 4, 10))
        self.assertEqual(rows[0].decision, "APPROVED")
        self.assertIsNone(rows[0].observations)

    def test_empty_results_and_all_three_query_plans(self) -> None:
        data = self._seed()
        empty_routines = asyncio.run(
            self._query("routines_by_program", RoutinesByProgramQuery(999999))
        )
        empty_usage = asyncio.run(
            self._query(
                "exercise_usage_by_program", ExerciseUsageByProgramQuery(999999)
            )
        )
        empty_reviews = asyncio.run(
            self._query("validations_by_reviewer", ValidationsByReviewerQuery(999999))
        )
        self.assertEqual(empty_routines, ())
        self.assertEqual(empty_usage, ())
        self.assertEqual(empty_reviews, ())

        params = (
            (data["program_id"], None, None, None, None),
            (data["program_id"], None, None, None, None),
            (data["reviewer_one"], None, None, None, None),
        )

        async def explain_plans():
            pool = await get_test_pool()
            plans = []
            sql_statements = (
                InformationalReportsSql.REP01_SQL,
                InformationalReportsSql.REP02_SQL,
                InformationalReportsSql.REP03_SQL,
            )
            async with pool.connection() as connection:
                for sql, query_params in zip(sql_statements, params, strict=True):
                    cursor = await connection.execute(
                        "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql,
                        query_params,
                    )
                    row = await cursor.fetchone()
                    plans.append(next(iter(row.values())))
            return plans

        plans = asyncio.run(explain_plans())
        self.assertEqual(len(plans), 3)
        self.assertTrue(all(plan for plan in plans))
