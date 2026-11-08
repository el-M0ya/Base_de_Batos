"""PostgreSQL implementation of ``ExerciseRepository`` (E2-06).

Design notes:

* all SQL is parameterized: no value is interpolated into the statement;
* every query that returns exercises joins the catalogs so a row can be mapped
  to domain value objects without guessing;
* duplicate detection uses the same rule as the domain: the *normalized* name
  plus the muscle group. The expression mirrors
  ``app.domain.entities.exercise.normalize_exercise_name`` (lowercase, remove
  Spanish diacritics, collapse whitespace) and is the one enforced by the unique
  index created in script ``009``;
* database errors are translated to application errors. Driver messages are
  never propagated: the application error carries a stable detail instead.
"""

from __future__ import annotations

from typing import Callable, Optional

import psycopg
from psycopg import AsyncConnection

from app.application.exceptions import (
    ApplicationError,
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.repositories.exercise_repository import ORDERING_FIELDS, ExerciseRepository
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel

ConnectionProvider = Callable[[], AsyncConnection]

_SELECT_COLUMNS = """
    e.id_exercise,
    e.name,
    e.description,
    e.registration_date,
    e.id_trainer_creator,
    et.name AS exercise_type_name,
    il.name AS intensity_name,
    mg.id_muscle_group,
    mg.name AS muscle_group_name
"""

_FROM_JOINED = """
    FROM exercise e
    JOIN exercise_type et ON et.id_exercise_type = e.id_exercise_type
    JOIN intensity_level il ON il.id_intensity_level = e.id_intensity_level
    JOIN muscle_group mg ON mg.id_muscle_group = e.id_muscle_group
"""

# Kept in sync with the unique index of script 009 and with the domain rule.
_NORMALIZED_NAME = (
    "lower(btrim(regexp_replace(translate(e.name, "
    "'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'), '\\s+', ' ', 'g')))"
)

_ORDER_BY = {
    "name": _NORMALIZED_NAME,
    "registration_date": "e.registration_date",
    "id_exercise": "e.id_exercise",
}


class PostgresExerciseRepository(ExerciseRepository):
    """Exercise repository backed by psycopg and the ``exercise`` table."""

    def __init__(self, connection_provider: ConnectionProvider) -> None:
        self._connection_provider = connection_provider

    # ------------------------------------------------------------------
    # ExerciseRepository
    # ------------------------------------------------------------------
    async def save(self, exercise: Exercise) -> Exercise:
        connection = self._connection_provider()
        try:
            async with connection.cursor() as cursor:
                exercise_type_id = await self._catalog_id(
                    cursor, "exercise_type", "id_exercise_type", exercise.exercise_type.value
                )
                intensity_id = await self._catalog_id(
                    cursor, "intensity_level", "id_intensity_level", exercise.intensity.value
                )

                if exercise.id_exercise is None:
                    await cursor.execute(
                        """
                        INSERT INTO exercise (
                            name, description, registration_date,
                            id_exercise_type, id_intensity_level,
                            id_muscle_group, id_trainer_creator
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id_exercise
                        """,
                        (
                            exercise.name,
                            exercise.description,
                            exercise.registration_date,
                            exercise_type_id,
                            intensity_id,
                            exercise.muscle_group.id_muscle_group,
                            exercise.id_trainer_creator,
                        ),
                    )
                    row = await cursor.fetchone()
                    return _replace_id(exercise, row["id_exercise"])

                await cursor.execute(
                    """
                    UPDATE exercise
                       SET name = %s,
                           description = %s,
                           registration_date = %s,
                           id_exercise_type = %s,
                           id_intensity_level = %s,
                           id_muscle_group = %s
                     WHERE id_exercise = %s
                    """,
                    (
                        exercise.name,
                        exercise.description,
                        exercise.registration_date,
                        exercise_type_id,
                        intensity_id,
                        exercise.muscle_group.id_muscle_group,
                        exercise.id_exercise,
                    ),
                )
                if cursor.rowcount == 0:
                    raise ResourceNotFound("exercise", exercise.id_exercise)
                return exercise
        except psycopg.Error as error:
            raise translate_database_error(error) from error

    async def get_by_id(self, id_exercise: int) -> Optional[Exercise]:
        connection = self._connection_provider()
        async with connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {_SELECT_COLUMNS} {_FROM_JOINED} WHERE e.id_exercise = %s",
                (id_exercise,),
            )
            row = await cursor.fetchone()
        return _row_to_exercise(row) if row else None

    async def find_duplicate(
        self, normalized_name: str, id_muscle_group: int
    ) -> Optional[Exercise]:
        connection = self._connection_provider()
        async with connection.cursor() as cursor:
            await cursor.execute(
                f"""
                SELECT {_SELECT_COLUMNS}
                {_FROM_JOINED}
                WHERE {_NORMALIZED_NAME} = %s
                  AND e.id_muscle_group = %s
                ORDER BY e.id_exercise
                LIMIT 1
                """,
                (normalized_name, id_muscle_group),
            )
            row = await cursor.fetchone()
        return _row_to_exercise(row) if row else None

    async def list(
        self,
        *,
        muscle_group_id: Optional[int] = None,
        exercise_type: Optional[ExerciseType] = None,
        intensity: Optional[IntensityLevel] = None,
        order_by: str = "name",
        descending: bool = False,
    ) -> list[Exercise]:
        if order_by not in ORDERING_FIELDS:
            raise InvalidInput(
                f"'order_by' must be one of {list(ORDERING_FIELDS)}, got {order_by!r}."
            )

        conditions: list[str] = []
        parameters: list[object] = []
        if muscle_group_id is not None:
            conditions.append("e.id_muscle_group = %s")
            parameters.append(muscle_group_id)
        if exercise_type is not None:
            conditions.append("et.name = %s")
            parameters.append(exercise_type.value)
        if intensity is not None:
            conditions.append("il.name = %s")
            parameters.append(intensity.value)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        direction = "DESC" if descending else "ASC"
        connection = self._connection_provider()
        async with connection.cursor() as cursor:
            await cursor.execute(
                f"""
                SELECT {_SELECT_COLUMNS}
                {_FROM_JOINED}
                {where}
                ORDER BY {_ORDER_BY[order_by]} {direction}, e.id_exercise
                """,
                tuple(parameters),
            )
            rows = await cursor.fetchall()
        return [_row_to_exercise(row) for row in rows]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    async def _catalog_id(cursor, table: str, column: str, name: str) -> int:
        await cursor.execute(f"SELECT {column} FROM {table} WHERE name = %s", (name,))
        row = await cursor.fetchone()
        if row is None:
            raise ResourceNotFound(table.replace("_", " "), name)
        return row[column]


def translate_database_error(error: psycopg.Error) -> ApplicationError:
    """Map a driver error to an application error without leaking its message."""
    if isinstance(error, psycopg.errors.UniqueViolation):
        return DuplicateResource(
            "exercise",
            "an exercise with the same normalized name already exists in that "
            "muscle group.",
        )
    if isinstance(error, psycopg.errors.ForeignKeyViolation):
        return ResourceNotFound(
            "referenced catalog or trainer",
            getattr(error.diag, "constraint_name", None) or "unknown",
        )
    if isinstance(error, (psycopg.errors.CheckViolation, psycopg.errors.NotNullViolation)):
        return InvalidInput(
            "a value violates a database CHECK or NOT NULL constraint "
            f"({getattr(error.diag, 'constraint_name', None) or 'unknown constraint'})."
        )
    return BusinessRuleViolation("the database rejected the operation.")


def _replace_id(exercise: Exercise, id_exercise: int) -> Exercise:
    from dataclasses import replace

    return replace(exercise, id_exercise=id_exercise)


def _row_to_exercise(row: dict) -> Exercise:
    """Map a joined row into a domain entity."""
    return Exercise(
        id_exercise=row["id_exercise"],
        name=row["name"],
        description=row["description"],
        registration_date=row["registration_date"],
        exercise_type=ExerciseType.from_value(row["exercise_type_name"]),
        intensity=IntensityLevel.from_value(row["intensity_name"]),
        muscle_group=MuscleGroup(
            id_muscle_group=row["id_muscle_group"],
            name=row["muscle_group_name"],
        ),
        id_trainer_creator=row["id_trainer_creator"],
    )
