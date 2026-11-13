"""SQL implementation of ``RoutineRepository`` over PostgreSQL with psycopg.

Persists and retrieves complete routines: header, generation parameters,
ordered exercise composition, JSONB nested structure, and validation history.

Every write happens inside a single ``TransactionManager`` block so that a
failure at any point rolls back every row across all involved tables
(routine, parameters_routine, contains, routine_structure, validate).

PostgreSQL driver errors are translated to application errors so callers
never see driver messages.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from psycopg.errors import (
    CheckViolation,
    ForeignKeyViolation,
    UniqueViolation,
)

from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.entities.routine_parameters import RoutineParameters
from app.domain.entities.routine_structure import RoutineStructure
from app.domain.entities.routine_validation import RoutineValidation, ValidationDecision
from app.domain.repositories.routine_repository import RoutineRepository
from app.application.ports.transaction_manager import TransactionManager
from app.infrastructure.persistence.jsonb_serializers import (
    jsonb_to_structure,
    structure_to_jsonb,
)


def _translate_error(error: Exception) -> Exception:
    """Translate a psycopg error into an application error."""
    detail = error.args[0] if error.args else ""
    if isinstance(error, UniqueViolation):
        return DuplicateResource("routine", detail)
    if isinstance(error, ForeignKeyViolation):
        if "workout_program" in detail:
            return ResourceNotFound("workout program", detail)
        if "trainer" in detail:
            return ResourceNotFound("trainer", detail)
        if "client" in detail:
            return ResourceNotFound("client", detail)
        if "exercise" in detail:
            return ResourceNotFound("exercise", detail)
        if "routine" in detail:
            return ResourceNotFound("routine", detail)
        if "room_chief" in detail:
            return ResourceNotFound("room chief", detail)
        return ResourceNotFound("reference", detail)
    if isinstance(error, CheckViolation):
        return InvalidInput(detail)
    return error


class RoutineRepositorySql(RoutineRepository):
    """PostgreSQL adapter of ``RoutineRepository``."""

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

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    async def save(
        self, routine: Routine, structure: RoutineStructure
    ) -> Routine:
        """Persist a routine with its complete variable structure atomically.

        Inserts into ``routine``, ``parameters_routine``, ``contains`` and
        ``routine_structure`` in a single transaction. A failure at any point
        rolls back every row.
        """
        try:
            # 1. Routine header
            cursor = await self._conn.execute(
                """
                INSERT INTO routine (
                    status,
                    creation_date,
                    id_workout_program,
                    id_trainer_creator,
                    id_client
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING id_routine, status, creation_date,
                          id_workout_program, id_trainer_creator, id_client
                """,
                (
                    routine.status.value,
                    routine.creation_date,
                    routine.id_workout_program,
                    routine.id_trainer_creator,
                    routine.id_client,
                ),
            )
            row = await cursor.fetchone()
            if row is None:
                raise InvalidInput("the routine insert did not return an identifier")
            routine_id = row["id_routine"]

            # 2. Generation parameters (one row per routine, U-8)
            params = getattr(routine, "_parameters", None)
            if params is None:
                raise InvalidInput("routine is missing generation parameters")
            await self._conn.execute(
                """
                INSERT INTO parameters_routine (
                    id_routine,
                    total_exercises,
                    intensity_level,
                    cardio_ratio,
                    strength_ratio,
                    flexibility_ratio,
                    covered_muscle_group_ids
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    routine_id,
                    params.total_exercises,
                    params.intensity_level.value,
                    str(params.cardio_ratio),
                    str(params.strength_ratio),
                    str(params.flexibility_ratio),
                    list(params.covered_muscle_group_ids),
                ),
            )

            # 3. Ordered exercise composition (CONTAINS)
            contains_rows = getattr(routine, "_contains", None)
            if not contains_rows:
                raise InvalidInput("a routine must contain at least one exercise")
            seen_orders: set[int] = set()
            seen_exercises: set[int] = set()
            for entry in contains_rows:
                order = entry["execution_order"]
                exercise_id = entry["id_exercise"]
                if order in seen_orders:
                    raise DuplicateResource(
                        "routine/execution order",
                        f"execution order {order} is repeated in routine {routine_id}.",
                    )
                if exercise_id in seen_exercises:
                    raise DuplicateResource(
                        "routine/exercise",
                        f"exercise {exercise_id} is repeated in routine {routine_id}.",
                    )
                seen_orders.add(order)
                seen_exercises.add(exercise_id)
                await self._conn.execute(
                    """
                    INSERT INTO contains (
                        id_routine, id_exercise, execution_order,
                        sets, repetitions, rest_time_seconds
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        routine_id,
                        exercise_id,
                        order,
                        entry["sets"],
                        entry["repetitions"],
                        entry.get("rest_time_seconds", 60),
                    ),
                )

            # 4. Variable nested structure (routine_structure, 1:1)
            structure_json = structure_to_jsonb(structure)
            await self._conn.execute(
                """
                INSERT INTO routine_structure (id_routine, structure_json)
                VALUES (%s, %s)
                """,
                (routine_id, structure_json),
            )

            saved = Routine(
                id_workout_program=routine.id_workout_program,
                id_trainer_creator=routine.id_trainer_creator,
                id_routine=routine_id,
                status=RoutineStatus(row["status"]),
                creation_date=row["creation_date"],
                id_client=row["id_client"],
                id_routine_origin=getattr(routine, "id_routine_origin", None),
            )
            return saved
        except (UniqueViolation, ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    # ------------------------------------------------------------------
    # Get complete
    # ------------------------------------------------------------------

    async def get_complete(
        self, id_routine: int
    ) -> Optional[tuple[Routine, RoutineStructure]]:
        """Return a routine and its complete structure, or ``None``."""
        try:
            cursor = await self._conn.execute(
                """
                SELECT r.id_routine, r.status, r.creation_date,
                       r.id_workout_program, r.id_trainer_creator, r.id_client
                FROM routine r
                WHERE r.id_routine = %s
                """,
                (id_routine,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None

            routine = Routine(
                id_workout_program=row["id_workout_program"],
                id_trainer_creator=row["id_trainer_creator"],
                id_routine=row["id_routine"],
                status=RoutineStatus(row["status"]),
                creation_date=row["creation_date"],
                id_client=row["id_client"],
            )

            # Parameters
            cursor = await self._conn.execute(
                """
                SELECT total_exercises, intensity_level, cardio_ratio,
                       strength_ratio, flexibility_ratio,
                       covered_muscle_group_ids
                FROM parameters_routine
                WHERE id_routine = %s
                """,
                (id_routine,),
            )
            params_row = await cursor.fetchone()
            if params_row is None:
                return None

            # Contains
            cursor = await self._conn.execute(
                """
                SELECT id_exercise, execution_order, sets, repetitions,
                       rest_time_seconds
                FROM contains
                WHERE id_routine = %s
                ORDER BY execution_order
                """,
                (id_routine,),
            )
            contains_rows = await cursor.fetchall()

            # Structure
            cursor = await self._conn.execute(
                """
                SELECT structure_json
                FROM routine_structure
                WHERE id_routine = %s
                """,
                (id_routine,),
            )
            struct_row = await cursor.fetchone()
            if struct_row is None:
                return None

            parameters = RoutineParameters(
                id_routine=id_routine,
                total_exercises=params_row["total_exercises"],
                intensity_level=params_row["intensity_level"],
                cardio_ratio=params_row["cardio_ratio"],
                strength_ratio=params_row["strength_ratio"],
                flexibility_ratio=params_row["flexibility_ratio"],
                covered_muscle_group_ids=params_row["covered_muscle_group_ids"],
            )
            routine._parameters = parameters
            routine._contains = [dict(entry) for entry in contains_rows]

            structure = jsonb_to_structure(id_routine, struct_row["structure_json"])

            return routine, structure
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    # ------------------------------------------------------------------
    # List by program
    # ------------------------------------------------------------------

    async def list_by_program(self, id_workout_program: int) -> list[Routine]:
        """Return routines belonging to a workout program."""
        try:
            cursor = await self._conn.execute(
                """
                SELECT id_routine, status, creation_date,
                       id_workout_program, id_trainer_creator, id_client
                FROM routine
                WHERE id_workout_program = %s
                ORDER BY creation_date DESC, id_routine DESC
                """,
                (id_workout_program,),
            )
            rows = await cursor.fetchall()
            return [
                Routine(
                    id_workout_program=row["id_workout_program"],
                    id_trainer_creator=row["id_trainer_creator"],
                    id_routine=row["id_routine"],
                    status=RoutineStatus(row["status"]),
                    creation_date=row["creation_date"],
                    id_client=row["id_client"],
                )
                for row in rows
            ]
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    # ------------------------------------------------------------------
    # Validations
    # ------------------------------------------------------------------

    async def save_validation(
        self, validation: RoutineValidation
    ) -> RoutineValidation:
        """Persist a routine validation and return the stored entity."""
        try:
            cursor = await self._conn.execute(
                """
                INSERT INTO validate (
                    id_routine,
                    id_room_chief,
                    fecha_validacion,
                    decision,
                    observaciones
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING id_validation, id_routine, id_room_chief,
                          fecha_validacion, decision, observaciones
                """,
                (
                    validation.id_routine,
                    validation.id_room_chief,
                    validation.validation_date,
                    validation.decision.value,
                    validation.observations,
                ),
            )
            row = await cursor.fetchone()
            if row is None:
                raise InvalidInput("the validation insert did not return an identifier")
            saved = RoutineValidation(
                id_routine=row["id_routine"],
                id_room_chief=row["id_room_chief"],
                decision=ValidationDecision(row["decision"]),
                id_validation=row["id_validation"],
                validation_date=row["validation_date"],
                observations=row["observaciones"],
            )
            return saved
        except (UniqueViolation, ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error

    async def list_validations(self, id_routine: int) -> list[RoutineValidation]:
        """Return the validation history of a routine."""
        try:
            cursor = await self._conn.execute(
                """
                SELECT id_validation, id_routine, id_room_chief,
                       fecha_validacion, decision, observaciones
                FROM validate
                WHERE id_routine = %s
                ORDER BY fecha_validacion DESC, id_validation DESC
                """,
                (id_routine,),
            )
            rows = await cursor.fetchall()
            return [
                RoutineValidation(
                    id_routine=row["id_routine"],
                    id_room_chief=row["id_room_chief"],
                    decision=ValidationDecision(row["decision"]),
                    id_validation=row["id_validation"],
                    validation_date=row["validation_date"],
                    observations=row["observaciones"],
                )
                for row in rows
            ]
        except (ForeignKeyViolation, CheckViolation) as error:
            raise _translate_error(error) from error
