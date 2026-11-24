"""Parameterized PostgreSQL read queries for reports REP-01 through REP-03."""

from __future__ import annotations

from app.application.dto.informational_report_dto import (
    ExerciseUsageByProgramQuery,
    ExerciseUsageReportRow,
    GeneratedRoutineReportRow,
    RoutinesByProgramQuery,
    ValidatedRoutineReportRow,
    ValidationsByReviewerQuery,
)
from app.application.ports.informational_reports import InformationalReportsQuery
from app.application.ports.transaction_manager import TransactionManager


class InformationalReportsSql(InformationalReportsQuery):
    """Read-only report adapter using the current request/test transaction."""

    REP01_SQL = """SELECT r.id_routine, r.status, r.id_trainer_creator,
                      u.name AS trainer_name, r.creation_date,
                      p.total_exercises, p.intensity_level,
                      p.cardio_ratio, p.strength_ratio, p.flexibility_ratio,
                      p.covered_muscle_group_ids
               FROM routine AS r
               JOIN trainer AS t ON t.id_trainer = r.id_trainer_creator
               JOIN app_user AS u ON u.id_user = t.id_trainer
               JOIN parameters_routine AS p ON p.id_routine = r.id_routine
               WHERE r.id_workout_program = %s
                 AND (%s::date IS NULL OR r.creation_date >= %s)
                 AND (%s::date IS NULL OR r.creation_date <= %s)
               ORDER BY r.creation_date DESC, r.id_routine DESC"""

    # This project has no exercise.intensity column. REP-02 therefore reports
    # the target intensity snapshot of each final routine.
    REP02_SQL = """SELECT e.id_exercise, e.name AS exercise_name,
                      p.intensity_level AS routine_intensity,
                      mg.id_muscle_group, mg.name AS muscle_group_name,
                      COUNT(*)::INTEGER AS usage_count
               FROM routine AS r
               JOIN parameters_routine AS p ON p.id_routine = r.id_routine
               JOIN contains AS c ON c.id_routine = r.id_routine
               JOIN exercise AS e ON e.id_exercise = c.id_exercise
               JOIN muscle_group AS mg ON mg.id_muscle_group = e.id_muscle_group
               WHERE r.id_workout_program = %s
                 AND r.status = 'APPROVED'
                 AND (%s::date IS NULL OR r.creation_date >= %s)
                 AND (%s::date IS NULL OR r.creation_date <= %s)
               GROUP BY e.id_exercise, e.name, p.intensity_level,
                        mg.id_muscle_group, mg.name
               ORDER BY usage_count DESC, e.name, p.intensity_level,
                        mg.name"""

    REP03_SQL = """SELECT v.id_validation, v.id_routine,
                      v.id_room_chief AS id_reviewer, u.name AS reviewer_name,
                      v.fecha_validacion AS validation_date,
                      v.decision, v.observaciones AS observations
               FROM validate AS v
               JOIN trainer AS t ON t.id_trainer = v.id_room_chief
               JOIN app_user AS u ON u.id_user = t.id_trainer
               WHERE v.id_room_chief = %s
                 AND (%s::date IS NULL OR v.fecha_validacion >= %s)
                 AND (%s::date IS NULL OR v.fecha_validacion <= %s)
               ORDER BY v.fecha_validacion DESC, v.id_validation DESC"""

    def __init__(self, transaction_manager: TransactionManager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        conn = self._tm.connection()
        if conn is None:
            raise RuntimeError(
                "No transaction active. Run report queries inside a "
                "TransactionManager block."
            )
        return conn

    async def routines_by_program(
        self, query: RoutinesByProgramQuery
    ) -> tuple[GeneratedRoutineReportRow, ...]:
        cursor = await self._conn.execute(
            self.REP01_SQL,
            (
                query.id_workout_program,
                query.start_date,
                query.start_date,
                query.end_date,
                query.end_date,
            ),
        )
        rows = await cursor.fetchall()
        return tuple(
            GeneratedRoutineReportRow(
                id_routine=row["id_routine"],
                status=row["status"],
                id_trainer_creator=row["id_trainer_creator"],
                trainer_name=row["trainer_name"],
                creation_date=row["creation_date"],
                total_exercises=row["total_exercises"],
                intensity_level=row["intensity_level"],
                cardio_ratio=row["cardio_ratio"],
                strength_ratio=row["strength_ratio"],
                flexibility_ratio=row["flexibility_ratio"],
                covered_muscle_group_ids=tuple(
                    row["covered_muscle_group_ids"] or ()
                ),
            )
            for row in rows
        )

    async def exercise_usage_by_program(
        self, query: ExerciseUsageByProgramQuery
    ) -> tuple[ExerciseUsageReportRow, ...]:
        cursor = await self._conn.execute(
            self.REP02_SQL,
            (
                query.id_workout_program,
                query.start_date,
                query.start_date,
                query.end_date,
                query.end_date,
            ),
        )
        return tuple(
            ExerciseUsageReportRow(
                id_exercise=row["id_exercise"],
                exercise_name=row["exercise_name"],
                routine_intensity=row["routine_intensity"],
                id_muscle_group=row["id_muscle_group"],
                muscle_group_name=row["muscle_group_name"],
                usage_count=row["usage_count"],
            )
            for row in await cursor.fetchall()
        )

    async def validations_by_reviewer(
        self, query: ValidationsByReviewerQuery
    ) -> tuple[ValidatedRoutineReportRow, ...]:
        cursor = await self._conn.execute(
            self.REP03_SQL,
            (
                query.id_reviewer,
                query.start_date,
                query.start_date,
                query.end_date,
                query.end_date,
            ),
        )
        return tuple(
            ValidatedRoutineReportRow(
                id_validation=row["id_validation"],
                id_routine=row["id_routine"],
                id_reviewer=row["id_reviewer"],
                reviewer_name=row["reviewer_name"],
                validation_date=row["validation_date"],
                decision=row["decision"],
                observations=row["observations"],
            )
            for row in await cursor.fetchall()
        )
