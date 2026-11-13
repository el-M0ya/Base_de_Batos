"""PostgreSQL implementations of ``CatalogRepository``.

The module exposes two adapters:

* ``CatalogRepositorySql`` participates in the request transaction and is used
  by the exercise reclassification slice.
* ``PostgresCatalogRepository`` receives a connection provider and is used by
  the exercise catalog composition.

Both read the same catalog tables, so keeping them in one module avoids
duplicating the row shapes and ordering rules.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional, TypedDict, cast

from psycopg import AsyncConnection

from app.application.ports.transaction_manager import TransactionManager
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.repositories.catalog_repository import CatalogRepository
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel

ConnectionProvider = Callable[[], AsyncConnection]


class _MuscleGroupRow(TypedDict):
    id_muscle_group: int
    name: str


class _CatalogValueRow(TypedDict):
    name: str


class CatalogRepositorySql(CatalogRepository):
    """Read-only catalog adapter backed by the request transaction manager."""

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


class PostgresCatalogRepository(CatalogRepository):
    """Read exercise catalogs from PostgreSQL through a connection provider."""

    def __init__(self, connection_provider: ConnectionProvider) -> None:
        self._connection_provider = connection_provider

    async def list_muscle_groups(self) -> list[MuscleGroup]:
        connection = self._connection_provider()
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT id_muscle_group, name
                  FROM muscle_group
                 ORDER BY name, id_muscle_group
                """
            )
            rows = cast(list[_MuscleGroupRow], await cursor.fetchall())
        return [
            MuscleGroup(
                id_muscle_group=row["id_muscle_group"],
                name=row["name"],
            )
            for row in rows
        ]

    async def get_muscle_group(self, id_muscle_group: int) -> MuscleGroup | None:
        connection = self._connection_provider()
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT id_muscle_group, name
                  FROM muscle_group
                 WHERE id_muscle_group = %s
                """,
                (id_muscle_group,),
            )
            row = cast(_MuscleGroupRow | None, await cursor.fetchone())
        if row is None:
            return None
        return MuscleGroup(
            id_muscle_group=row["id_muscle_group"],
            name=row["name"],
        )

    async def list_exercise_types(self) -> list[ExerciseType]:
        connection = self._connection_provider()
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT name
                  FROM exercise_type
                 ORDER BY name
                """
            )
            rows = cast(list[_CatalogValueRow], await cursor.fetchall())
        return [ExerciseType.from_value(row["name"]) for row in rows]

    async def list_intensity_levels(self) -> list[IntensityLevel]:
        connection = self._connection_provider()
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT name
                  FROM intensity_level
                 ORDER BY name
                """
            )
            rows = cast(list[_CatalogValueRow], await cursor.fetchall())
        return [IntensityLevel.from_value(row["name"]) for row in rows]
