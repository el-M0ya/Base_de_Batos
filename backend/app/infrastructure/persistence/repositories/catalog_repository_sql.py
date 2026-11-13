"""PostgreSQL implementation of the exercise catalog repository."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypedDict, cast

from psycopg import AsyncConnection

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


class PostgresCatalogRepository(CatalogRepository):
    """Read exercise catalogs from PostgreSQL."""

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
