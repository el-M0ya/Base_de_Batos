"""PostgreSQL implementation of ``WorkoutProgramRepository``.

Programs and their ``covers`` rows are written in the same transaction. The
adapter deletes the previous coverage before inserting the new one, so a failed
association rolls back the whole unit of work. Deleting a program removes its
coverage first and still lets the database reject the deletion when another
relation (authorisations, enrolments or routines) references the program.
"""

from __future__ import annotations

from datetime import date
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
from app.domain.entities.authorisation import Authorisation
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.workout_program import WorkoutProgram
from app.domain.repositories.workout_program_repository import (
    WorkoutProgramRepository,
)


def _row_to_program(row: dict, groups: list[MuscleGroup]) -> WorkoutProgram:
    """Map a program row and its coverage to the domain entity."""
    return WorkoutProgram(
        id_workout_program=row["id_workout_program"],
        name=row["name"],
        objective=row["objective"],
        target_muscle_groups=groups,
    )


def _translate_error(error: Exception) -> Exception:
    """Translate a psycopg error into an application error."""
    detail = error.args[0] if error.args else ""
    if isinstance(error, UniqueViolation):
        return DuplicateResource("training program", detail)
    if isinstance(error, (ForeignKeyViolation, RestrictViolation)):
        return BusinessRuleViolation(
            "the training program cannot be deleted because authorisations, "
            "enrolments or routines reference it; remove those references first."
        )
    if isinstance(error, CheckViolation):
        return InvalidInput(detail)
    return error


class WorkoutProgramRepositorySql(WorkoutProgramRepository):
    """PostgreSQL adapter of ``WorkoutProgramRepository``."""

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

    async def save(self, program: WorkoutProgram) -> WorkoutProgram:
        """Insert or update a program and replace its covered muscle groups."""
        try:
            if program.id_workout_program is None:
                cursor = await self._conn.execute(
                    """
                    INSERT INTO workout_program (name, objective)
                    VALUES (%s, %s)
                    RETURNING id_workout_program, name, objective
                    """,
                    (program.name, program.objective),
                )
            else:
                cursor = await self._conn.execute(
                    """
                    UPDATE workout_program
                    SET name = %s,
                        objective = %s
                    WHERE id_workout_program = %s
                    RETURNING id_workout_program, name, objective
                    """,
                    (
                        program.name,
                        program.objective,
                        program.id_workout_program,
                    ),
                )

            row = await cursor.fetchone()
            if row is None:
                raise ResourceNotFound(
                    "training program", program.id_workout_program
                )
        except (UniqueViolation, CheckViolation) as error:
            raise _translate_error(error) from error

        await self._replace_coverage(row["id_workout_program"], program)
        return _row_to_program(row, list(program.target_muscle_groups))

    async def _replace_coverage(
        self, id_workout_program: int, program: WorkoutProgram
    ) -> None:
        """Delete the previous coverage and insert the requested one."""
        await self._conn.execute(
            "DELETE FROM covers WHERE id_workout_program = %s",
            (id_workout_program,),
        )
        try:
            for group in program.target_muscle_groups:
                if group.id_muscle_group is None:
                    raise InvalidInput(
                        "every covered muscle group must be persisted"
                    )
                await self._conn.execute(
                    """
                    INSERT INTO covers (id_workout_program, id_muscle_group)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (id_workout_program, group.id_muscle_group),
                )
        except ForeignKeyViolation as error:
            raise ResourceNotFound(
                "muscle group",
                "one of the requested muscle groups does not exist",
            ) from error

    async def get_by_id(
        self, id_workout_program: int
    ) -> Optional[WorkoutProgram]:
        """Return a program with its coverage, or ``None``."""
        cursor = await self._conn.execute(
            """
            SELECT id_workout_program, name, objective
            FROM workout_program
            WHERE id_workout_program = %s
            """,
            (id_workout_program,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        groups = await self.list_covered_muscle_groups(id_workout_program)
        return _row_to_program(row, groups)

    async def get_by_name(self, name: str) -> Optional[WorkoutProgram]:
        """Return a program by case-insensitive, trimmed name."""
        cursor = await self._conn.execute(
            """
            SELECT id_workout_program, name, objective
            FROM workout_program
            WHERE LOWER(BTRIM(name)) = LOWER(BTRIM(%s))
            """,
            (name,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        groups = await self.list_covered_muscle_groups(row["id_workout_program"])
        return _row_to_program(row, groups)

    async def list(self) -> list[WorkoutProgram]:
        """Return every program ordered by name."""
        cursor = await self._conn.execute(
            """
            SELECT id_workout_program, name, objective
            FROM workout_program
            ORDER BY name ASC
            """
        )
        rows = await cursor.fetchall()
        programs: list[WorkoutProgram] = []
        for row in rows:
            groups = await self.list_covered_muscle_groups(
                row["id_workout_program"]
            )
            programs.append(_row_to_program(row, groups))
        return programs

    async def delete(self, id_workout_program: int) -> None:
        """Delete a program and its coverage, preserving other references."""
        try:
            await self._conn.execute(
                "DELETE FROM covers WHERE id_workout_program = %s",
                (id_workout_program,),
            )
            cursor = await self._conn.execute(
                """
                DELETE FROM workout_program
                WHERE id_workout_program = %s
                RETURNING id_workout_program
                """,
                (id_workout_program,),
            )
            row = await cursor.fetchone()
            if row is None:
                raise ResourceNotFound("training program", id_workout_program)
        except (ForeignKeyViolation, RestrictViolation) as error:
            raise _translate_error(error) from error

    async def list_covered_muscle_groups(
        self, id_workout_program: int
    ) -> list[MuscleGroup]:
        """Return the muscle groups covered by a program, ordered by name."""
        cursor = await self._conn.execute(
            """
            SELECT mg.id_muscle_group, mg.name
            FROM covers AS c
            JOIN muscle_group AS mg
              ON mg.id_muscle_group = c.id_muscle_group
            WHERE c.id_workout_program = %s
            ORDER BY mg.name ASC
            """,
            (id_workout_program,),
        )
        rows = await cursor.fetchall()
        return [
            MuscleGroup(
                id_muscle_group=row["id_muscle_group"],
                name=row["name"],
            )
            for row in rows
        ]

    async def is_client_enrolled(
        self, id_client: int, id_workout_program: int, on_date: Optional[date] = None
    ) -> bool:
        """Return whether a client is enrolled in a program."""
        cursor = await self._conn.execute(
            """
            SELECT 1
            FROM inscribed
            WHERE id_client = %s
              AND id_workout_program = %s
              AND (%s::date IS NULL OR enrollment_date <= %s)
            LIMIT 1
            """,
            (id_client, id_workout_program, on_date, on_date),
        )
        return await cursor.fetchone() is not None

    async def get_authorisation(
        self, id_trainer: int, id_workout_program: int
    ) -> Optional[Authorisation]:
        """Return a trainer's authorization for a program, or ``None``."""
        cursor = await self._conn.execute(
            """
            SELECT id_trainer, id_workout_program, can_generate,
                   can_validate, start_date, end_date
            FROM authorises
            WHERE id_trainer = %s AND id_workout_program = %s
            """,
            (id_trainer, id_workout_program),
        )
        row = await cursor.fetchone()
        return None if row is None else Authorisation(**row)
