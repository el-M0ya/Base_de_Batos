"""Parameterized PostgreSQL queries for informational reports REP-04–REP-06."""

from __future__ import annotations

from app.application.dto.informational_performance_report_dto import (
    AbandonmentRankingReport,
    AdjustmentCohortComparisonRow,
    IntensityPerformanceCorrelationRow,
    ProgramDistributionQuery,
    ProgramDistributionRow,
    RoutinePerformanceQuery,
    RoutinePerformanceRow,
)
from app.application.ports.informational_performance_reports import (
    InformationalPerformanceReportsQuery,
)
from app.application.ports.transaction_manager import TransactionManager


class InformationalPerformanceReportsSql(InformationalPerformanceReportsQuery):
    REP04_SQL = """SELECT r.id_routine, p.intensity_level,
        a.id_client, u.name AS client_name,
        COALESCE(array_agg(DISTINCT e.id_exercise) FILTER (WHERE e.id_exercise IS NOT NULL), '{}') AS exercise_ids,
        COALESCE(array_agg(DISTINCT e.name) FILTER (WHERE e.name IS NOT NULL), '{}') AS exercise_names,
        COUNT(DISTINCT s.id_session)::INTEGER AS session_count,
        COUNT(DISTINCT s.id_session) FILTER (WHERE s.completada)::INTEGER AS completed_session_count,
        AVG(CASE WHEN s.id_session IS NOT NULL THEN s.completada::INTEGER::NUMERIC END) AS completion_rate
      FROM routine r
      LEFT JOIN parameters_routine p ON p.id_routine = r.id_routine
      LEFT JOIN contains c ON c.id_routine = r.id_routine
      LEFT JOIN exercise e ON e.id_exercise = c.id_exercise
      LEFT JOIN assignment a ON a.id_routine = r.id_routine
      LEFT JOIN client cl ON cl.id_client = a.id_client
      LEFT JOIN app_user u ON u.id_user = cl.id_client
      LEFT JOIN session s ON s.id_assignment = a.id_assignment
      WHERE r.id_routine = %s
      GROUP BY r.id_routine, p.intensity_level, a.id_client, u.name
      ORDER BY a.id_client NULLS FIRST"""

    REP05_SQL = """SELECT wp.id_workout_program, wp.name AS program_name,
        mg.id_muscle_group, mg.name AS muscle_group_name,
        p.intensity_level,
        COUNT(c.id_exercise)::INTEGER AS exercise_count,
        COUNT(DISTINCT r.id_routine)::INTEGER AS routine_count,
        NULL::BOOLEAN AS balance_criteria_met,
        'CRITERIA_UNSPECIFIED'::TEXT AS balance_status
      FROM workout_program wp
      LEFT JOIN routine r ON r.id_workout_program = wp.id_workout_program
      LEFT JOIN parameters_routine p ON p.id_routine = r.id_routine
      LEFT JOIN contains c ON c.id_routine = r.id_routine
      LEFT JOIN exercise e ON e.id_exercise = c.id_exercise
      LEFT JOIN muscle_group mg ON mg.id_muscle_group = e.id_muscle_group
      GROUP BY wp.id_workout_program, wp.name, mg.id_muscle_group, mg.name, p.intensity_level
      ORDER BY wp.name, mg.name NULLS FIRST, p.intensity_level NULLS FIRST"""

    REP06A_SQL = """WITH client_performance AS (
        SELECT r.id_routine, r.id_workout_program, p.intensity_level,
          AVG(CASE WHEN s.id_session IS NOT NULL THEN s.completada::INTEGER::NUMERIC END) AS completion_rate
        FROM routine r
        JOIN parameters_routine p ON p.id_routine = r.id_routine
        JOIN assignment a ON a.id_routine = r.id_routine
        JOIN session s ON s.id_assignment = a.id_assignment
        GROUP BY r.id_routine, r.id_workout_program, p.intensity_level, a.id_client
      ), points AS (
        SELECT id_workout_program, completion_rate,
          CASE lower(btrim(intensity_level))
            WHEN 'bajo' THEN 1.0 WHEN 'low' THEN 1.0
            WHEN 'medio' THEN 2.0 WHEN 'medium' THEN 2.0
            WHEN 'alto' THEN 3.0 WHEN 'high' THEN 3.0
            ELSE NULL
          END AS intensity_score
        FROM client_performance
      )
      SELECT wp.id_workout_program, wp.name AS program_name,
        corr(points.intensity_score::DOUBLE PRECISION,
             points.completion_rate::DOUBLE PRECISION) AS correlation,
        COUNT(points.intensity_score)::INTEGER AS observation_count,
        CASE WHEN COUNT(points.intensity_score) < 2 THEN 'INSUFFICIENT_DATA'
             WHEN corr(points.intensity_score::DOUBLE PRECISION,
                       points.completion_rate::DOUBLE PRECISION) IS NULL THEN 'NO_VARIANCE'
             ELSE 'CALCULATED' END AS calculation_status
      FROM workout_program wp
      LEFT JOIN points ON points.id_workout_program = wp.id_workout_program
      GROUP BY wp.id_workout_program, wp.name
      ORDER BY wp.name"""

    REP06C_SQL = """WITH client_rates AS (
        SELECT a.id_client, r.id_workout_program, cl.id_site,
          AVG(s.completada::INTEGER::NUMERIC) AS completion_rate
        FROM assignment a
        JOIN routine r ON r.id_routine = a.id_routine
        JOIN client cl ON cl.id_client = a.id_client
        JOIN session s ON s.id_assignment = a.id_assignment
        GROUP BY a.id_client, r.id_workout_program, cl.id_site
      ), cohorts AS (
        SELECT DISTINCT req.id_client, r.id_workout_program
        FROM request req JOIN routine r ON r.id_routine = req.id_routine
      ), cohort_rates AS (
        SELECT cr.id_site, cr.id_workout_program,
          COUNT(DISTINCT cr.id_client)::INTEGER AS client_count,
          AVG(cr.completion_rate) AS cohort_rate
        FROM client_rates cr
        JOIN cohorts co ON co.id_client = cr.id_client
                       AND co.id_workout_program = cr.id_workout_program
        GROUP BY cr.id_site, cr.id_workout_program
      ), site_rates AS (
        SELECT id_site, id_workout_program, AVG(completion_rate) AS site_rate
        FROM client_rates GROUP BY id_site, id_workout_program
      )
      SELECT s.id_site, s.name AS site_name, wp.id_workout_program,
        wp.name AS program_name, co.client_count AS adjustment_client_count,
        co.cohort_rate AS adjustment_cohort_completion_rate,
        sr.site_rate AS site_average_completion_rate
      FROM cohort_rates co
      JOIN site_rates sr USING (id_site, id_workout_program)
      JOIN site s ON s.id_site = co.id_site
      JOIN workout_program wp ON wp.id_workout_program = co.id_workout_program
      ORDER BY s.name, wp.name"""

    def __init__(self, transaction_manager: TransactionManager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        conn = self._tm.connection()
        if conn is None:
            raise RuntimeError("Run informational report queries inside a transaction.")
        return conn

    async def routine_performance(self, query: RoutinePerformanceQuery):
        cursor = await self._conn.execute(self.REP04_SQL, (query.id_routine,))
        return tuple(
            RoutinePerformanceRow(
                id_routine=r["id_routine"],
                intensity_level=r["intensity_level"],
                id_client=r["id_client"],
                client_name=r["client_name"],
                exercise_ids=tuple(r["exercise_ids"] or ()),
                exercise_names=tuple(r["exercise_names"] or ()),
                session_count=r["session_count"],
                completed_session_count=r["completed_session_count"],
                completion_rate=r["completion_rate"],
            )
            for r in await cursor.fetchall()
        )

    async def program_distributions(self, query: ProgramDistributionQuery):
        del query
        cursor = await self._conn.execute(self.REP05_SQL)
        return tuple(ProgramDistributionRow(**r) for r in await cursor.fetchall())

    async def intensity_performance_correlations(self):
        cursor = await self._conn.execute(self.REP06A_SQL)
        return tuple(
            IntensityPerformanceCorrelationRow(**r) for r in await cursor.fetchall()
        )

    async def exercise_abandonment_ranking(self):
        return AbandonmentRankingReport(
            available=False,
            status="DEFINITION_PENDING",
            reason=(
                "Exercise abandonment cannot be calculated: sessions store a single "
                "completion flag for the whole session. Instructors must define the "
                "exercise-level rate before ranking exercises."
            ),
        )

    async def adjustment_cohort_comparisons(self):
        cursor = await self._conn.execute(self.REP06C_SQL)
        return tuple(
            AdjustmentCohortComparisonRow(**r) for r in await cursor.fetchall()
        )
