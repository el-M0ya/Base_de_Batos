"""PostgreSQL adapter for routine assignments (RF-28, R5, U-9).

The repository uses the connection held by the request transaction manager, so
its reads and writes join the same unit of work as the other repositories used
by the assignment use case. Driver errors are translated to the application
error hierarchy used by the rest of the persistence layer.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation

from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.application.ports.transaction_manager import TransactionManager
from app.domain.entities.assignment import Assignment
from app.domain.repositories.assignment_repository import AssignmentRepository


_ASSIGNMENT_COLUMNS = """
    id_assignment, id_routine, id_client,
    fecha_asignacion AS assignment_date, fecha_fin AS end_date
"""


def _translate_error(error: Exception) -> Exception:
    """Translate a psycopg error into an application error."""
    detail = error.args[0] if error.args else ""
    constraint = ""
    if hasattr(error, "diag"):
        constraint = getattr(error.diag, "constraint_name", None) or ""

    if isinstance(error, UniqueViolation):
        return DuplicateResource(
            "assignment",
            "the routine has already been assigned to this client",
        )
    if isinstance(error, ForeignKeyViolation):
        if "routine" in constraint or "routine" in detail:
            return ResourceNotFound("routine", detail)
        if "client" in constraint or "client" in detail:
            return ResourceNotFound("client", detail)
        return ResourceNotFound("reference", detail)
    if isinstance(error, CheckViolation):
        return InvalidInput("the assignment end date cannot precede its start date")
    return error


class AssignmentRepositorySql(AssignmentRepository):
    """SQL implementation of ``AssignmentRepository``."""

    def __init__(self, transaction_manager: TransactionManager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        connection = self._tm.connection()
        if connection is None:
            raise RuntimeError(
                "No transaction active. Use the repository inside a "
                "TransactionManager block."
            )
        return connection

    async def find_by_routine_and_client(
        self, id_routine: int, id_client: int
    ) -> Optional[Assignment]:
        """Return the assignment for a routine/client pair, if it exists."""
        try:
            cursor = await self._conn.execute(
                f"""SELECT {_ASSIGNMENT_COLUMNS}
                    FROM assignment
                    WHERE id_routine = %s AND id_client = %s
                    ORDER BY id_assignment DESC
                    LIMIT 1""",
                (id_routine, id_client),
            )
            row = await cursor.fetchone()
            return Assignment(**row) if row is not None else None
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    async def list_active_for_client(
        self, id_client: int, on_date: Optional[date] = None
    ) -> list[Assignment]:
        """Return the client's assignments active on the requested date."""
        reference = on_date or date.today()
        try:
            cursor = await self._conn.execute(
                f"""SELECT {_ASSIGNMENT_COLUMNS}
                    FROM assignment
                    WHERE id_client = %s
                      AND fecha_asignacion <= %s
                      AND (fecha_fin IS NULL OR fecha_fin >= %s)
                    ORDER BY fecha_asignacion DESC, id_assignment DESC""",
                (id_client, reference, reference),
            )
            return [Assignment(**row) for row in await cursor.fetchall()]
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    async def save(self, assignment: Assignment) -> Assignment:
        """Insert an assignment and return it with its generated identifier."""
        try:
            cursor = await self._conn.execute(
                """
                INSERT INTO assignment (
                    id_routine, id_client, fecha_asignacion, fecha_fin
                ) VALUES (%s, %s, %s, %s)
                RETURNING id_assignment, id_routine, id_client,
                          fecha_asignacion AS assignment_date,
                          fecha_fin AS end_date
                """,
                (
                    assignment.id_routine,
                    assignment.id_client,
                    assignment.assignment_date,
                    assignment.end_date,
                ),
            )
            row = await cursor.fetchone()
            if row is None:
                raise RuntimeError("The assignment insert returned no row.")
            return Assignment(**row)
        except (UniqueViolation, ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error
