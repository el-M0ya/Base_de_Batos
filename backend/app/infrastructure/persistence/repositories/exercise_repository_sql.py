"""SQL implementation of ``ExerciseRepository`` over PostgreSQL with psycopg.

All queries are explicit and parameterized. Repository instances obtain their
connection from a per-request :class:`app.application.ports.transaction_manager.TransactionManager`,
so several repositories can join the same transaction without the application
layer knowing psycopg.

PostgreSQL driver errors are translated to application errors so callers never
see driver messages.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from psycopg.errors import (
    CheckViolation,
    ForeignKeyViolation,
    UniqueViolation,
)
from psycopg.rows import dict_row

from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.domain.entities.exercise import Exercise, normalize_exercise_name
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.repositories.exercise_repository import (
    ExerciseRepository,
    ORDERING_FIELDS,
)
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.application.ports.transaction_manager import TransactionManager

# Ensure the ``intensity`` column exists on the exercise table. The original
# schema (script 003) predates this epic; the column is added idempotently so
# the repository can persist and read the exercise intensity.
ENSURE_INTENSITY_COLUMN = """
    ALTER TABLE exercise
    ADD COLUMN IF NOT EXISTS intensity VARCHAR(20) NOT NULL DEFAULT 'medio'
"""

# ``user`` is a reserved word in PostgreSQL; quote it when referenced.
_QUOTED_USER = '"user"'

_BASE_SELECT = """
    SELECT
        e.id_exercise,
        e.name,
        e.description,
        e.registration_date,
        e.id_exercise_type,
        et.name AS exercise_type_name,
        e.id_muscle_group,
        mg.name AS muscle_group_name,
        e.id_trainer_creator,
        e.intensity
    FROM exercise e
    JOIN exercise_type et ON et.id_exercise_type = e.id_exercise_type
    JOIN muscle_group mg ON mg.id_muscle_group = e.id_muscle_group
"""

_INSERT_SQL = """
    INSERT INTO exercise (
        name,
        description,
        registration_date,
        id_exercise_type,
        id_muscle_group,
        id_trainer_creator,
        intensity
    ) VALUES (
        %s,
        %s,
        %s,
        (SELECT id_exercise_type FROM exercise_type WHERE name = %s),
        %s,
        %s,
        %s
    )
    RETURNING id_exercise
"""


def _row_to_exercise(row: dict) -> Exercise:
    """Map a database row (dict_row) to an ``Exercise`` domain entity."""
    return Exercise(
        name=row["name"],
        exercise_type=ExerciseType.from_value(row["exercise_type_name"]),
        intensity=IntensityLevel.from_value(row["intensity"]),
        muscle_group=MuscleGroup(
            id_muscle_group=row["id_muscle_group"],
            name=row["muscle_group_name"],
        ),
        id_trainer_creator=row["id_trainer_creator"],
        id_exercise=row["id_exercise"],
        description=row["description"],
        registration_date=row["registration_date"],
    )


def _translate_error(error: Exception) -> Exception:
    """Translate a psycopg error into an application error."""
    if isinstance(error, UniqueViolation):
        constraint = getattr(error, "diag", None)
        constraint_name = getattr(constraint, "constraint_name", None) if constraint else None
        detail = error.args[0] if error.args else ""
        if constraint_name == "uq_exercise_identity" or "uq_exercise_identity" in detail:
            return DuplicateResource(
                "exercise",
                "an exercise with the same normalized name already exists in this muscle group.",
            )
        return DuplicateResource("exercise", detail)
    if isinstance(error, ForeignKeyViolation):
        detail = error.args[0] if error.args else ""
        if "muscle_group" in detail:
            return ResourceNotFound("muscle group", detail)
        if "trainer" in detail or "trainers" in detail:
            return ResourceNotFound("trainer", detail)
        if "exercise_type" in detail:
            return ResourceNotFound("exercise type", detail)
        return ResourceNotFound("reference", detail)
    if isinstance(error, CheckViolation):
        return InvalidInput(error.args[0] if error.args else "check constraint violated")
    return error


class ExerciseRepositorySql(ExerciseRepository):
    """PostgreSQL adapter of ``ExerciseRepository``."""

    def __init__(self, transaction_manager: TransactionManager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        conn = self._tm.connection()
        if conn is None:
            raise RuntimeError(
                "No transaction active. Use the repository inside a TransactionManager block."
            )
        return conn

    async def save(self, exercise: Exercise) -> Exercise:
        """Insert the exercise when it has no identifier, update it otherwise."""
        try:
            await self._conn.execute(ENSURE_INTENSITY_COLUMN)
            if exercise.id_exercise is None:
                cursor = await self._conn.execute(
                    _INSERT_SQL,
                    (
                        exercise.name,
                        exercise.description,
                        exercise.registration_date,
                        exercise.exercise_type.value,
                        exercise.muscle_group.id_muscle_group,
                        exercise.id_trainer_creator,
                        exercise.intensity.value,
                    ),
                )
                row = await cursor.fetchone()
                if row is None:
                    raise InvalidInput("the insert did not return an identifier")
                saved = replace_with_id(exercise, row["id_exercise"])
            else:
                await self._conn.execute(
                    """
                    UPDATE exercise
                    SET name = %s,
                        description = %s,
                        registration_date = %s,
                        id_exercise_type = (SELECT id_exercise_type FROM exercise_type WHERE name = %s),
                        id_muscle_group = %s,
                        id_trainer_creator = %s,
                        intensity = %s
                    WHERE id_exercise = %s
                    """,
                    (
                        exercise.name,
                        exercise.description,
                        exercise.registration_date,
                        exercise.exercise_type.value,
                        exercise.muscle_group.id_muscle_group,
                        exercise.id_trainer_creator,
                        exercise.intensity.value,
                        exercise.id_exercise,
                    ),
                )
                saved = exercise
            return saved
        except (UniqueViolation, ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    async def get_by_id(self, id_exercise: int) -> Optional[Exercise]:
        """Return the exercise with that identifier, or ``None``."""
        try:
            cursor = await self._conn.execute(
                _BASE_SELECT + " WHERE e.id_exercise = %s",
                (id_exercise,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return _row_to_exercise(row)
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    async def find_duplicate(
        self, normalized_name: str, id_muscle_group: int
    ) -> Optional[Exercise]:
        """Return the exercise that collides with the duplicate key (U-12).

        Duplicate detection uses the normalized name and the muscle group, so
        the same name in another muscle group is not a duplicate.
        """
        try:
            cursor = await self._conn.execute(
                _BASE_SELECT + " WHERE e.id_muscle_group = %s",
                (id_muscle_group,),
            )
            rows = await cursor.fetchall()
            for row in rows:
                entity = _row_to_exercise(row)
                if entity.normalized_name == normalized_name:
                    return entity
            return None
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    async def list(
        self,
        *,
        muscle_group_id: Optional[int] = None,
        exercise_type: Optional[ExerciseType] = None,
        intensity: Optional[IntensityLevel] = None,
        order_by: str = "name",
        descending: bool = False,
    ) -> list[Exercise]:
        """Return the exercises that match the optional filters (RF-13)."""
        if order_by not in ORDERING_FIELDS:
            raise InvalidInput(
                f"'order_by' must be one of {list(ORDERING_FIELDS)}, got {order_by!r}."
            )

        conditions: list[str] = []
        params: list = []

        if muscle_group_id is not None:
            conditions.append("e.id_muscle_group = %s")
            params.append(muscle_group_id)
        if exercise_type is not None:
            conditions.append("et.name = %s")
            params.append(exercise_type.value)
        if intensity is not None:
            conditions.append("e.intensity = %s")
            params.append(intensity.value)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        order_column = order_by
        if order_column == "name":
            order_column = "e.name"
        elif order_column == "registration_date":
            order_column = "e.registration_date"
        elif order_column == "id_exercise":
            order_column = "e.id_exercise"

        direction = "DESC" if descending else "ASC"

        sql = f"""
            {_BASE_SELECT}
            {where_clause}
            ORDER BY {order_column} {direction}
        """
        try:
            cursor = await self._conn.execute(sql, tuple(params))
            rows = await cursor.fetchall()
            return [_row_to_exercise(row) for row in rows]
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error


def replace_with_id(exercise: Exercise, id_exercise: int) -> Exercise:
    """Return a copy of ``exercise`` with the given identifier assigned."""
    from dataclasses import replace

    return replace(exercise, id_exercise=id_exercise)
