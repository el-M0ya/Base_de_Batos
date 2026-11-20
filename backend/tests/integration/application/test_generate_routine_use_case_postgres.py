"""PostgreSQL integration tests for the routine-generation use case (E6-02).

The tests build the real SQL repositories, execute the use case inside one
transaction manager, and verify the complete aggregate in the database. A second
test forces a foreign-key failure after the header and parameters were inserted
and verifies that the transaction manager rolls every row back.
"""

from __future__ import annotations

import asyncio
import unittest
from contextlib import AsyncExitStack
from datetime import date
from decimal import Decimal
from typing import Optional

import psycopg
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from backend.tests.integration.base import IntegrationTestCase
from backend.tests.integration.support.builders import (
    build_muscle_group,
    build_workout_program,
)
from backend.tests.integration.support.database import (
    _target_db_dsn,
    get_test_pool,
)
from app.application.ports.transaction_manager import TransactionManager
from backend.tests.unit.application.fakes.in_memory_exercise_repository import (
    InMemoryExerciseRepository,
)
from app.application.dto.actor import ActorDTO
from app.application.dto.routine_generation_dto import GenerateRoutineInputDTO
from app.application.exceptions import ResourceNotFound
from app.application.use_cases.generate_routine import GenerateRoutineUseCase
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.strategies.balanced_strategy import BalancedRoutineGenerationStrategy
from app.domain.strategies.strategy_registry import StrategyRegistry
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence.repositories.routine_repository_sql import (
    RoutineRepositorySql,
)
from app.infrastructure.persistence.repositories.workout_program_repository_sql import (
    WorkoutProgramRepositorySql,
)


TRAINER_ID = 1001
PROGRAM_ID = 501
GENERATION_DATE = date(2026, 5, 1)


class _TestPoolTransactionManager(TransactionManager):
    """Transaction manager that borrows connections from the test pool.

    The integration base keeps its own pool, while the production transaction
    manager uses the application pool. Using the test pool directly keeps the
    integration test isolated without changing production wiring.
    """

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool
        self._connection: Optional[AsyncConnection] = None
        self._stack: Optional[AsyncExitStack] = None

    async def __aenter__(self) -> "TransactionManager":
        self._stack = AsyncExitStack()
        self._connection = await self._stack.enter_async_context(
            self._pool.connection()
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._stack is None:
            return
        stack = self._stack
        self._stack = None
        self._connection = None
        await stack.__aexit__(exc_type, exc_val, exc_tb)

    def connection(self) -> Optional[AsyncConnection]:
        return self._connection


def _connect() -> psycopg.Connection:
    """Open an autocommit connection to the dedicated test database."""
    return psycopg.connect(_target_db_dsn(), autocommit=True)


def _execute(sql: str, params: tuple = ()) -> None:
    """Run a statement that does not need a result."""
    conn = _connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
    finally:
        conn.close()


def _fetch_one(sql: str, params: tuple = ()) -> tuple:
    """Run a query and return its first row."""
    conn = _connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if row is None:
                raise AssertionError("the query returned no rows")
            return row
    finally:
        conn.close()


def _fetch_all(sql: str, params: tuple = ()) -> list[tuple]:
    """Run a query and return every row."""
    conn = _connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


class GenerateRoutineUseCasePostgresTests(IntegrationTestCase):
    """Complete persistence and rollback tests against PostgreSQL."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls._test_pool = asyncio.run(get_test_pool())

    def transaction_manager(self) -> TransactionManager:
        """Use the test pool instead of the application-wide pool."""
        return _TestPoolTransactionManager(self._test_pool)

    def _seed_trainer_and_program(
        self, *, covered: bool = True
    ) -> tuple[int, MuscleGroup]:
        """Insert a trainer, program, authorisation, and optional coverage."""
        chest = build_muscle_group(id_muscle_group=1, name="Chest")
        build_workout_program(
            id_workout_program=PROGRAM_ID,
            name="Strength Base",
            objective="General strength",
        )
        _execute(
            """
            INSERT INTO app_user (id_user, name, email, password_hash, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                TRAINER_ID,
                "Integration Trainer",
                "integration.trainer@example.com",
                "not-a-real-hash",
                "TRAINER",
            ),
        )
        _execute(
            "INSERT INTO trainer (id_trainer, specialty) VALUES (%s, %s)",
            (TRAINER_ID, "GENERAL"),
        )
        if covered:
            _execute(
                """
                INSERT INTO covers (id_workout_program, id_muscle_group)
                VALUES (%s, %s)
                """,
                (PROGRAM_ID, chest.id_muscle_group),
            )
        _execute(
            """
            INSERT INTO authorises (
                id_trainer, id_workout_program, can_generate, can_validate,
                start_date, end_date
            ) VALUES (%s, %s, TRUE, FALSE, %s, NULL)
            """,
            (TRAINER_ID, PROGRAM_ID, date(2026, 1, 1)),
        )
        return PROGRAM_ID, chest

    def _seed_catalogs(self) -> None:
        """Restore the exercise types removed by the test table cleaner."""
        _execute(
            """
            INSERT INTO exercise_type (name)
            VALUES ('fuerza'), ('cardio'), ('flexibilidad')
            ON CONFLICT (name) DO NOTHING
            """
        )

    async def _seed_exercises(self, chest: MuscleGroup) -> None:
        """Insert the exercise bank through the real SQL repository."""
        tm = self.transaction_manager()
        async with tm:
            repo = self.exercise_repository(tm)
            for name, exercise_type in (
                ("Bench Press", ExerciseType.STRENGTH),
                ("Push Up", ExerciseType.STRENGTH),
                ("Jump Rope", ExerciseType.CARDIO),
                ("Rowing", ExerciseType.CARDIO),
            ):
                await repo.save(
                    Exercise(
                        name=name,
                        exercise_type=exercise_type,
                        intensity=IntensityLevel.HIGH,
                        muscle_group=chest,
                        id_trainer_creator=TRAINER_ID,
                    )
                )

    async def _execute_use_case(
        self,
        use_case_input: GenerateRoutineInputDTO,
        *,
        exercise_repository=None,
    ):
        """Run the use case with SQL collaborators inside one transaction."""
        tm = self.transaction_manager()
        programs = WorkoutProgramRepositorySql(tm)
        exercises = exercise_repository or self.exercise_repository(tm)
        routines = RoutineRepositorySql(tm)
        use_case = GenerateRoutineUseCase(
            programs,
            exercises,
            routines,
            StrategyRegistry([BalancedRoutineGenerationStrategy()]),
        )
        async with tm:
            return await use_case.execute(use_case_input)

    async def _fetch_complete(self, id_routine: int):
        """Read the aggregate back through the repository."""
        tm = self.transaction_manager()
        async with tm:
            return await RoutineRepositorySql(tm).get_complete(id_routine)

    def _input(self) -> GenerateRoutineInputDTO:
        """Build a request whose proportions match the seeded bank."""
        return GenerateRoutineInputDTO(
            actor=ActorDTO(id_user=TRAINER_ID, role=UserRole.TRAINER),
            id_workout_program=PROGRAM_ID,
            strategy_name="balanced",
            total_exercises=2,
            target_intensity=IntensityLevel.HIGH,
            exercise_type_proportions={
                ExerciseType.STRENGTH: Decimal("0.5"),
                ExerciseType.CARDIO: Decimal("0.5"),
            },
            generation_date=GENERATION_DATE,
        )

    def test_generates_and_persists_complete_routine(self) -> None:
        _, chest = self._seed_trainer_and_program()
        self._seed_catalogs()
        asyncio.run(self._seed_exercises(chest))

        result = asyncio.run(self._execute_use_case(self._input()))

        self.assertIsNotNone(result.routine.id_routine)
        self.assertEqual(result.routine.status.value, "DRAFT")
        self.assertEqual(result.routine.id_workout_program, PROGRAM_ID)
        self.assertEqual(result.routine.id_trainer_creator, TRAINER_ID)
        self.assertEqual(result.routine.creation_date, GENERATION_DATE)
        self.assertEqual(result.parameters.covered_muscle_group_ids, [1])
        self.assertEqual(len(result.composition), 2)
        self.assertEqual(len(result.structure.blocks), 2)

        routine_row = _fetch_one(
            """
            SELECT status, creation_date, id_workout_program,
                   id_trainer_creator, id_client
            FROM routine
            WHERE id_routine = %s
            """,
            (result.routine.id_routine,),
        )
        self.assertEqual(routine_row[0], "DRAFT")
        self.assertEqual(routine_row[1], GENERATION_DATE)
        self.assertEqual(routine_row[2], PROGRAM_ID)
        self.assertEqual(routine_row[3], TRAINER_ID)
        self.assertIsNone(routine_row[4])

        parameters_row = _fetch_one(
            """
            SELECT total_exercises, intensity_level, cardio_ratio,
                   strength_ratio, flexibility_ratio, covered_muscle_group_ids
            FROM parameters_routine
            WHERE id_routine = %s
            """,
            (result.routine.id_routine,),
        )
        self.assertEqual(parameters_row[0], 2)
        self.assertEqual(parameters_row[1], "HIGH")
        self.assertEqual(parameters_row[2], Decimal("50.00"))
        self.assertEqual(parameters_row[3], Decimal("50.00"))
        self.assertEqual(parameters_row[4], Decimal("0.00"))
        self.assertEqual(parameters_row[5], [1])

        contains_rows = _fetch_all(
            """
            SELECT id_exercise, execution_order, sets, repetitions,
                   rest_time_seconds
            FROM contains
            WHERE id_routine = %s
            ORDER BY execution_order
            """,
            (result.routine.id_routine,),
        )
        self.assertEqual(len(contains_rows), 2)
        self.assertEqual([row[1] for row in contains_rows], [1, 2])
        self.assertTrue(all(row[2] == 3 for row in contains_rows))
        self.assertTrue(all(row[3] == 10 for row in contains_rows))
        self.assertTrue(all(row[4] == 60 for row in contains_rows))

        structure_row = _fetch_one(
            """
            SELECT structure_json
            FROM routine_structure
            WHERE id_routine = %s
            """,
            (result.routine.id_routine,),
        )
        self.assertEqual(len(structure_row[0]["blocks"]), 2)
        self.assertTrue(
            all(
                block["block_type"] == "SET"
                for block in structure_row[0]["blocks"]
            )
        )

        fetched = asyncio.run(self._fetch_complete(result.routine.id_routine))
        self.assertIsNotNone(fetched)
        fetched_routine, fetched_structure = fetched
        self.assertEqual(fetched_routine.id_routine, result.routine.id_routine)
        self.assertEqual(
            fetched_structure.to_dict(),
            result.structure.to_dict(),
        )
        self.assertEqual(
            fetched_routine._parameters.covered_muscle_group_ids,
            [1],
        )
        self.assertEqual(len(fetched_routine._contains), 2)

    def test_rolls_back_every_table_when_persistence_fails(self) -> None:
        _, chest = self._seed_trainer_and_program()
        ghost = Exercise(
            id_exercise=999999,
            name="Ghost Exercise",
            exercise_type=ExerciseType.STRENGTH,
            intensity=IntensityLevel.HIGH,
            muscle_group=chest,
            id_trainer_creator=TRAINER_ID,
        )
        use_case_input = GenerateRoutineInputDTO(
            actor=ActorDTO(id_user=TRAINER_ID, role=UserRole.TRAINER),
            id_workout_program=PROGRAM_ID,
            strategy_name="balanced",
            total_exercises=1,
            target_intensity=IntensityLevel.HIGH,
            exercise_type_proportions={ExerciseType.STRENGTH: Decimal("1")},
            generation_date=GENERATION_DATE,
        )

        with self.assertRaises(ResourceNotFound):
            asyncio.run(
                self._execute_use_case(
                    use_case_input,
                    exercise_repository=InMemoryExerciseRepository([ghost]),
                )
            )

        counts = _fetch_one(
            """
            SELECT
                (SELECT COUNT(*) FROM routine),
                (SELECT COUNT(*) FROM parameters_routine),
                (SELECT COUNT(*) FROM contains),
                (SELECT COUNT(*) FROM routine_structure)
            """
        )
        self.assertEqual(counts, (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
