"""PostgreSQL adapter for program-scoped routine consultation."""

from __future__ import annotations

from datetime import date

from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.repositories.routine_consultation_repository import (
    RoutineConsultationRepository,
)


class RoutineConsultationRepositorySql(RoutineConsultationRepository):
    """Read-only routine query with authorization enforced in SQL."""

    def __init__(self, transaction_manager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        connection = self._tm.connection()
        if connection is None:
            raise RuntimeError(
                "No transaction active for routine consultation persistence."
            )
        return connection

    async def is_authorized_for_program(
        self,
        id_trainer: int,
        id_workout_program: int,
        on_date: date,
    ) -> bool:
        cursor = await self._conn.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM authorises
                WHERE id_trainer = %s
                  AND id_workout_program = %s
                  AND start_date <= %s
                  AND (end_date IS NULL OR end_date >= %s)
            ) AS is_authorized
            """,
            (id_trainer, id_workout_program, on_date, on_date),
        )
        row = await cursor.fetchone()
        return bool(row["is_authorized"])

    async def list_for_trainer(
        self,
        id_trainer: int,
        id_workout_program: int,
        on_date: date,
    ) -> list[Routine]:
        cursor = await self._conn.execute(
            """
            SELECT r.id_routine, r.status, r.creation_date,
                   r.id_workout_program, r.id_trainer_creator, r.id_client
            FROM routine AS r
            WHERE r.id_workout_program = %s
              AND r.id_trainer_creator <> %s
              AND EXISTS (
                  SELECT 1
                  FROM authorises AS requester_authorisation
                  WHERE requester_authorisation.id_trainer = %s
                    AND requester_authorisation.id_workout_program =
                        r.id_workout_program
                    AND requester_authorisation.start_date <= %s
                    AND (
                        requester_authorisation.end_date IS NULL
                        OR requester_authorisation.end_date >= %s
                    )
              )
              AND EXISTS (
                  SELECT 1
                  FROM authorises AS creator_authorisation
                  WHERE creator_authorisation.id_trainer =
                        r.id_trainer_creator
                    AND creator_authorisation.id_workout_program =
                        r.id_workout_program
                    AND creator_authorisation.start_date <= %s
                    AND (
                        creator_authorisation.end_date IS NULL
                        OR creator_authorisation.end_date >= %s
                    )
              )
            ORDER BY r.creation_date DESC, r.id_routine DESC
            """,
            (
                id_workout_program,
                id_trainer,
                id_trainer,
                on_date,
                on_date,
                on_date,
                on_date,
            ),
        )
        rows = await cursor.fetchall()
        return [
            Routine(
                id_routine=row["id_routine"],
                status=RoutineStatus(row["status"]),
                creation_date=row["creation_date"],
                id_workout_program=row["id_workout_program"],
                id_trainer_creator=row["id_trainer_creator"],
                id_client=row["id_client"],
            )
            for row in rows
        ]
