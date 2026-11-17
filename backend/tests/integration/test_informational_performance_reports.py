"""Integration coverage for informational reports REP-04 through REP-06."""

from __future__ import annotations

import asyncio
from datetime import date, time
from decimal import Decimal
from uuid import uuid4

import pytest

pytest.importorskip("psycopg")
pytest.importorskip("psycopg_pool")

import psycopg

from app.application.dto.informational_performance_report_dto import (
    ProgramDistributionQuery,
    RoutinePerformanceQuery,
)
from app.infrastructure.persistence.queries.informational_performance_reports_sql import (
    InformationalPerformanceReportsSql,
)
from backend.tests.integration.base import IntegrationTestCase
from backend.tests.integration.support.database import _target_db_dsn, get_test_pool


class _BoundTransaction:
    def __init__(self, connection) -> None:
        self._connection = connection

    def connection(self):
        return self._connection


class InformationalPerformanceReportsIntegrationTests(IntegrationTestCase):
    def _seed(self) -> dict[str, int]:
        suffix = uuid4().hex[:10]
        with psycopg.connect(_target_db_dsn(), autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO site (name, address) VALUES (%s, 'Test') RETURNING id_site",
                    (f"Site {suffix}",),
                )
                site_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO app_user (name,email,password_hash,role) VALUES (%s,%s,'x','TRAINER') RETURNING id_user",
                    (f"Trainer {suffix}", f"trainer-{suffix}@example.test"),
                )
                trainer_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO trainer (id_trainer,specialty) VALUES (%s,'GENERAL')",
                    (trainer_id,),
                )
                client_ids = []
                for label in ("A", "B"):
                    cur.execute(
                        "INSERT INTO app_user (name,email,password_hash,role) VALUES (%s,%s,'x','CLIENT') RETURNING id_user",
                        (
                            f"Client {label} {suffix}",
                            f"client-{label}-{suffix}@example.test",
                        ),
                    )
                    client_id = cur.fetchone()[0]
                    cur.execute(
                        "INSERT INTO client (id_client,age,id_site) VALUES (%s,30,%s)",
                        (client_id, site_id),
                    )
                    client_ids.append(client_id)
                cur.execute(
                    "INSERT INTO workout_program (name,objective) VALUES (%s,'Report test') RETURNING id_workout_program",
                    (f"Program {suffix}",),
                )
                program_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO workout_program (name,objective) VALUES (%s,'No routines') RETURNING id_workout_program",
                    (f"Empty {suffix}",),
                )
                empty_program_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO muscle_group (name) VALUES (%s) RETURNING id_muscle_group",
                    (f"Muscle {suffix}",),
                )
                muscle_id = cur.fetchone()[0]
                cur.execute(
                    "SELECT id_exercise_type FROM exercise_type WHERE name='fuerza'"
                )
                type_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO exercise (name,registration_date,id_exercise_type,id_muscle_group,id_trainer_creator) VALUES (%s,CURRENT_DATE,%s,%s,%s) RETURNING id_exercise",
                    (f"Exercise {suffix}", type_id, muscle_id, trainer_id),
                )
                exercise_id = cur.fetchone()[0]
                routine_ids = []
                for index, intensity in enumerate(("bajo", "medio", "alto"), 1):
                    cur.execute(
                        "INSERT INTO routine (status,creation_date,id_workout_program,id_trainer_creator) VALUES ('APPROVED',CURRENT_DATE,%s,%s) RETURNING id_routine",
                        (program_id, trainer_id),
                    )
                    routine_id = cur.fetchone()[0]
                    routine_ids.append(routine_id)
                    cur.execute(
                        "INSERT INTO parameters_routine (id_routine,total_exercises,intensity_level,cardio_ratio,strength_ratio,flexibility_ratio,covered_muscle_group_ids) VALUES (%s,1,%s,0,100,0,%s)",
                        (routine_id, intensity, [muscle_id]),
                    )
                    cur.execute(
                        "INSERT INTO contains (id_routine,id_exercise,execution_order,sets,repetitions,rest_time_seconds) VALUES (%s,%s,1,1,1,0)",
                        (routine_id, exercise_id),
                    )
                    for client_index, client_id in enumerate(client_ids):
                        cur.execute(
                            "INSERT INTO assignment (id_routine,id_client,fecha_asignacion) VALUES (%s,%s,CURRENT_DATE) RETURNING id_assignment",
                            (routine_id, client_id),
                        )
                        assignment_id = cur.fetchone()[0]
                        total = 2
                        completed = (index - 1) if client_index == 0 else 2
                        for session_index in range(total):
                            cur.execute(
                                "INSERT INTO session (id_assignment,fecha_sesion,hora_inicio,hora_fin,completada) VALUES (%s,%s,%s,%s,%s)",
                                (
                                    assignment_id,
                                    date(2026, 1, 1 + session_index),
                                    time(9),
                                    time(10),
                                    session_index < completed,
                                ),
                            )
                cur.execute(
                    "INSERT INTO request (id_client,id_routine,id_trainer,fecha_solicitud,motivo,estado) VALUES (%s,%s,%s,CURRENT_DATE,'test','OPEN')",
                    (client_ids[0], routine_ids[0], trainer_id),
                )
        return {
            "site": site_id,
            "program": program_id,
            "empty_program": empty_program_id,
            "routine": routine_ids[1],
        }

    def test_reports_cover_data_and_explicit_unknown_definitions(self) -> None:
        data = self._seed()

        async def read_reports():
            pool = await get_test_pool()
            async with pool.connection() as connection:
                reports = InformationalPerformanceReportsSql(
                    _BoundTransaction(connection)
                )
                async with connection.transaction():
                    routine = await reports.routine_performance(
                        RoutinePerformanceQuery(data["routine"])
                    )
                    distributions = await reports.program_distributions(
                        ProgramDistributionQuery()
                    )
                    correlations = await reports.intensity_performance_correlations()
                    abandonment = await reports.exercise_abandonment_ranking()
                    comparisons = await reports.adjustment_cohort_comparisons()
                return routine, distributions, correlations, abandonment, comparisons

        routine, distributions, correlations, abandonment, comparisons = asyncio.run(
            read_reports()
        )
        self.assertEqual(routine[0].session_count, 2)
        self.assertEqual(routine[0].completion_rate, Decimal("0.5"))
        self.assertTrue(
            any(
                row.id_workout_program == data["empty_program"]
                and row.routine_count == 0
                for row in distributions
            )
        )
        correlation = next(
            row for row in correlations if row.id_workout_program == data["program"]
        )
        self.assertEqual(correlation.observation_count, 6)
        self.assertEqual(correlation.calculation_status, "CALCULATED")
        self.assertFalse(abandonment.available)
        self.assertEqual(abandonment.status, "DEFINITION_PENDING")
        comparison = next(
            row for row in comparisons if row.id_workout_program == data["program"]
        )
        self.assertEqual(comparison.adjustment_client_count, 1)
        self.assertEqual(comparison.adjustment_cohort_completion_rate, Decimal("0.5"))
        self.assertEqual(comparison.site_average_completion_rate, Decimal("0.75"))
