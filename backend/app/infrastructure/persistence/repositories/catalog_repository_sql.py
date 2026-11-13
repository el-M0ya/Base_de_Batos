"""SQL implementation of ``CatalogRepository`` over PostgreSQL with psycopg.

The adapter reads the catalog tables used by the exercise form and by the
existence checks performed before creating or reclassifying an exercise. It
uses the connection held by the request transaction manager so it participates
in the same unit of work as the exercise repository.
"""

from __future__ import annotations

from typing import Optional

from app.application.ports.transaction_manager import TransactionManager
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.repositories.catalog_repository import CatalogRepository
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel


class CatalogRepositorySql(CatalogRepository):
    """Read-only catalog adapter backed by PostgreSQL."""

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

    async def list_muscle_groups(self) -> list[MuscleGroup]:
        """Return every muscle group ordered by name."""
        cursor = await self._conn.execute(
            "SELECT id_muscle_group, name FROM muscle_group ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [
            MuscleGroup(
                id_muscle_group=row["id_muscle_group"],
                name=row["name"],
            )
            for row in rows
        ]

    async def get_muscle_group(self, id_muscle_group: int) -> Optional[MuscleGroup]:
        """Return the muscle group with that identifier, or ``None``."""
        cursor = await self._conn.execute(
            "SELECT id_muscle_group, name FROM muscle_group "
            "WHERE id_muscle_group = %s",
            (id_muscle_group,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return MuscleGroup(
            id_muscle_group=row["id_muscle_group"],
            name=row["name"],
        )

    async def list_exercise_types(self) -> list[ExerciseType]:
        """Return the exercise types seeded in the database catalog."""
        cursor = await self._conn.execute(
            "SELECT name FROM exercise_type ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [ExerciseType.from_value(row["name"]) for row in rows]

    async def list_intensity_levels(self) -> list[IntensityLevel]:
        """Return the intensity levels of the approved catalog.

        The current schema models intensity as an attribute of routines and
        exercises, not as a physical ``intensity_level`` table. The domain enum
        is therefore the source of truth for this catalog and mirrors the
        values seeded by script ``008``.
        """
        return list(IntensityLevel)
