"""PostgreSQL adapter for routine assignment persistence."""

from __future__ import annotations

from datetime import date

from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation

from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.domain.entities.assignment import Assignment
from app.domain.repositories.assignment_repository import AssignmentRepository
from app.infrastructure.persistence.transaction import PsqlTransactionManager


class AssignmentRepositorySql(AssignmentRepository):
    """Read and write assignments using the request's shared transaction."""

    def __init__(self, transaction_manager: PsqlTransactionManager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        conn = self._tm.connection()
        if conn is None:
            raise RuntimeError("No transaction active for assignment persistence.")
        return conn

    @staticmethod
    def _from_row(row) -> Assignment:
        return Assignment(
            id_assignment=row["id_assignment"],
            id_routine=row["id_routine"],
            id_client=row["id_client"],
            assignment_date=row["fecha_asignacion"],
            end_date=row["fecha_fin"],
        )

    async def get_by_id(self, id_assignment: int) -> Assignment | None:
        cursor = await self._conn.execute(
            """SELECT id_assignment, id_routine, id_client,
                      fecha_asignacion, fecha_fin
               FROM assignment WHERE id_assignment = %s""",
            (id_assignment,),
        )
        row = await cursor.fetchone()
        return self._from_row(row) if row else None

    async def find_by_routine_and_client(
        self, id_routine: int, id_client: int
    ) -> Assignment | None:
        cursor = await self._conn.execute(
            """SELECT id_assignment, id_routine, id_client,
                      fecha_asignacion, fecha_fin
               FROM assignment WHERE id_routine = %s AND id_client = %s""",
            (id_routine, id_client),
        )
        row = await cursor.fetchone()
        return self._from_row(row) if row else None

    async def list_active_for_client(
        self, id_client: int, on_date: date | None = None
    ) -> list[Assignment]:
        reference_date = on_date or date.today()
        cursor = await self._conn.execute(
            """SELECT id_assignment, id_routine, id_client,
                      fecha_asignacion, fecha_fin
               FROM assignment
               WHERE id_client = %s
                 AND fecha_asignacion <= %s
                 AND (fecha_fin IS NULL OR fecha_fin >= %s)
               ORDER BY fecha_asignacion DESC, id_assignment DESC""",
            (id_client, reference_date, reference_date),
        )
        return [self._from_row(row) for row in await cursor.fetchall()]

    async def save(self, assignment: Assignment) -> Assignment:
        try:
            cursor = await self._conn.execute(
                """INSERT INTO assignment
                       (id_routine, id_client, fecha_asignacion, fecha_fin)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id_assignment, id_routine, id_client,
                             fecha_asignacion, fecha_fin""",
                (
                    assignment.id_routine,
                    assignment.id_client,
                    assignment.assignment_date,
                    assignment.end_date,
                ),
            )
            row = await cursor.fetchone()
            if row is None:
                raise InvalidInput("the assignment insert returned no row")
            return self._from_row(row)
        except UniqueViolation as error:
            raise DuplicateResource(
                "assignment", "this routine is already assigned to the client"
            ) from error
        except ForeignKeyViolation as error:
            constraint = error.diag.constraint_name
            if constraint == "fk_assignment_routine":
                raise ResourceNotFound("routine", assignment.id_routine) from error
            if constraint == "fk_assignment_client":
                raise ResourceNotFound("client", assignment.id_client) from error
            raise
        except CheckViolation as error:
            raise InvalidInput("assignment dates are invalid") from error
