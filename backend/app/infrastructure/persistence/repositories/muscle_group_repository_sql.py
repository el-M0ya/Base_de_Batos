"""PostgreSQL implementation of ``MuscleGroupRepository``.

The adapter uses the connection held by the request transaction manager so
several repositories can participate in the same unit of work. Names are
compared case-insensitively after trimming to enforce U-3 at the application
boundary, while the database keeps its unique constraint as the final guard.
"""

from __future__ import annotations

from typing import Optional

from psycopg.errors import (
    CheckViolation,
    ForeignKeyViolation,
    RestrictViolation,
    UniqueViolation,
)

from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.application.ports.transaction_manager import TransactionManager
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.repositories.muscle_group_repository import MuscleGroupRepository


def _row_to_muscle_group(row: dict) -> MuscleGroup:
    """Map a database row (dict_row) to the domain entity."""
    return MuscleGroup(
        id_muscle_group=row["id_muscle_group"],
        name=row["name"],
    )


def _translate_error(error: Exception) -> Exception:
    """Translate a psycopg error into an application error."""
    detail = error.args[0] if error.args else ""
    if isinstance(error, UniqueViolation):
        return DuplicateResource("muscle group", detail)
    if isinstance(error, (ForeignKeyViolation, RestrictViolation)):
        return BusinessRuleViolation(
            "the muscle group cannot be deleted because exercises or training "
            "programs reference it; remove those references first."
        )
    if isinstance(error, CheckViolation):
        return InvalidInput(detail)
    return error


class MuscleGroupRepositorySql(MuscleGroupRepository):
    """PostgreSQL adapter of ``MuscleGroupRepository``."""

    def __init__(self, transaction_manager: TransactionManager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        conn = self._tm.connection()
        if conn is None:
            raise RuntimeError(
                "No transaction active. Use the repository inside a "
                "TransactionManager block."
            )
        return conn

    async def save(self, muscle_group: MuscleGroup) -> MuscleGroup:
        """Insert a new catalog entry or update an existing one."""
        try:
            if muscle_group.id_muscle_group is None:
                cursor = await self._conn.execute(
                    """
                    INSERT INTO muscle_group (name)
                    VALUES (%s)
                    RETURNING id_muscle_group, name
                    """,
                    (muscle_group.name,),
                )
            else:
                cursor = await self._conn.execute(
                    """
                    UPDATE muscle_group
                    SET name = %s
                    WHERE id_muscle_group = %s
                    RETURNING id_muscle_group, name
                    """,
                    (muscle_group.name, muscle_group.id_muscle_group),
                )

            row = await cursor.fetchone()
            if row is None:
                raise ResourceNotFound(
                    "muscle group", muscle_group.id_muscle_group
                )
            return _row_to_muscle_group(row)
        except (UniqueViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    async def get_by_id(self, id_muscle_group: int) -> Optional[MuscleGroup]:
        """Return the catalog entry with that identifier, or ``None``."""
        cursor = await self._conn.execute(
            """
            SELECT id_muscle_group, name
            FROM muscle_group
            WHERE id_muscle_group = %s
            """,
            (id_muscle_group,),
        )
        row = await cursor.fetchone()
        return None if row is None else _row_to_muscle_group(row)

    async def get_by_name(self, name: str) -> Optional[MuscleGroup]:
        """Return a catalog entry by case-insensitive, trimmed name."""
        cursor = await self._conn.execute(
            """
            SELECT id_muscle_group, name
            FROM muscle_group
            WHERE LOWER(BTRIM(name)) = LOWER(BTRIM(%s))
            """,
            (name,),
        )
        row = await cursor.fetchone()
        return None if row is None else _row_to_muscle_group(row)

    async def list(self) -> list[MuscleGroup]:
        """Return every catalog entry ordered by name."""
        cursor = await self._conn.execute(
            """
            SELECT id_muscle_group, name
            FROM muscle_group
            ORDER BY name ASC
            """
        )
        rows = await cursor.fetchall()
        return [_row_to_muscle_group(row) for row in rows]

    async def delete(self, id_muscle_group: int) -> None:
        """Delete a catalog entry, failing when a relation references it."""
        try:
            cursor = await self._conn.execute(
                """
                DELETE FROM muscle_group
                WHERE id_muscle_group = %s
                RETURNING id_muscle_group
                """,
                (id_muscle_group,),
            )
            row = await cursor.fetchone()
            if row is None:
                raise ResourceNotFound("muscle group", id_muscle_group)
        except (ForeignKeyViolation, RestrictViolation) as error:
            raise _translate_error(error) from error
