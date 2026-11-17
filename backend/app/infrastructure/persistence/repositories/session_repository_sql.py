"""PostgreSQL adapter for completed training sessions."""

from __future__ import annotations

from datetime import date

from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation

from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.domain.entities.training_session import TrainingSession
from app.domain.repositories.session_repository import SessionRepository
from app.infrastructure.persistence.transaction import PsqlTransactionManager


class SessionRepositorySql(SessionRepository):
    """Persist sessions while keeping the client derived from assignment."""

    def __init__(self, transaction_manager: PsqlTransactionManager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        conn = self._tm.connection()
        if conn is None:
            raise RuntimeError("No transaction active for session persistence.")
        return conn

    @staticmethod
    def _from_row(row) -> TrainingSession:
        perceived = row["intensidad_percibida"]
        return TrainingSession(
            id_session=row["id_session"],
            id_assignment=row["id_assignment"],
            session_date=row["fecha_sesion"],
            start_time=row["hora_inicio"],
            end_time=row["hora_fin"],
            intensity_perceived=int(perceived) if perceived is not None else None,
            completed=row["completada"],
            observations=row["observaciones"],
        )

    async def save(self, session: TrainingSession) -> TrainingSession:
        try:
            cursor = await self._conn.execute(
                """INSERT INTO session (
                       id_assignment, fecha_sesion, hora_inicio, hora_fin,
                       intensidad_percibida, completada, observaciones
                   ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                   RETURNING id_session, id_assignment, fecha_sesion,
                             hora_inicio, hora_fin, intensidad_percibida,
                             completada, observaciones""",
                (
                    session.id_assignment,
                    session.session_date,
                    session.start_time,
                    session.end_time,
                    (
                        str(session.intensity_perceived)
                        if session.intensity_perceived is not None
                        else None
                    ),
                    session.completed,
                    session.observations,
                ),
            )
            row = await cursor.fetchone()
            if row is None:
                raise InvalidInput("the session insert returned no row")
            return self._from_row(row)
        except UniqueViolation as error:
            raise DuplicateResource(
                "session",
                "a session already exists for this assignment on this date",
            ) from error
        except ForeignKeyViolation as error:
            if error.diag.constraint_name == "fk_session_assignment":
                raise ResourceNotFound("assignment", session.id_assignment) from error
            raise
        except CheckViolation as error:
            raise InvalidInput(
                "the session fields violate a database constraint"
            ) from error

    async def find_by_assignment_and_date(
        self, id_assignment: int, session_date: date
    ) -> TrainingSession | None:
        cursor = await self._conn.execute(
            """SELECT id_session, id_assignment, fecha_sesion, hora_inicio,
                      hora_fin, intensidad_percibida, completada, observaciones
               FROM session WHERE id_assignment = %s AND fecha_sesion = %s""",
            (id_assignment, session_date),
        )
        row = await cursor.fetchone()
        return self._from_row(row) if row else None

    async def list_by_assignment(self, id_assignment: int) -> list[TrainingSession]:
        cursor = await self._conn.execute(
            """SELECT id_session, id_assignment, fecha_sesion, hora_inicio,
                      hora_fin, intensidad_percibida, completada, observaciones
               FROM session WHERE id_assignment = %s
               ORDER BY fecha_sesion DESC, hora_inicio DESC, id_session DESC""",
            (id_assignment,),
        )
        return [self._from_row(row) for row in await cursor.fetchall()]
