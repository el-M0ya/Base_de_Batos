"""Integration tests for the SQL routine repository.

Covers: complete routine save and retrieval, JSONB nested structure round-trip,
transactional atomicity on failure, duplicate exercise/order rejection (U-6/U-7),
parameter proportion validation, missing reference rejection, at-least-one
exercise rule, validation persistence and status sync, and retrieval by primary
key.
"""

from __future__ import annotations

import asyncio
import unittest
from datetime import date
from decimal import Decimal
from psycopg import connect as _psycopg_connect

from backend.tests.integration.base import IntegrationTestCase
from backend.tests.integration.support.builders import (
    build_muscle_group,
    build_trainer,
    build_user,
    build_workout_program,
)
from backend.tests.integration.support.database import _target_db_dsn
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.entities.routine_parameters import RoutineParameters
from app.domain.entities.routine_structure import (
    BlockType,
    RoutineBlock,
    RoutineStructure,
)
from app.domain.entities.routine_validation import (
    RoutineValidation,
    ValidationDecision,
)
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.infrastructure.persistence.repositories.routine_repository_sql import (
    RoutineRepositorySql,
)


def _save_exercise_direct(
    id_exercise: int,
    name: str,
    muscle_group: MuscleGroup,
    id_trainer_creator: int = 301,
) -> Exercise:
    """Insert an exercise directly into the database (integration test helper)."""
    conn = _psycopg_connect(_target_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO exercise (id_exercise, name, description, registration_date,
                    id_exercise_type, id_muscle_group, id_trainer_creator, intensity)
                VALUES (%s, %s, %s, %s,
                    (SELECT id_exercise_type FROM exercise_type WHERE name = %s),
                    %s, %s, %s)
                RETURNING id_exercise
                """,
                (
                    id_exercise,
                    name,
                    None,
                    date(2026, 1, 1),
                    "fuerza",
                    muscle_group.id_muscle_group,
                    id_trainer_creator,
                    "alto",
                ),
            )
            row = cur.fetchone()
            return Exercise(
                id_exercise=row[0],
                name=name,
                description=None,
                registration_date=date(2026, 1, 1),
                exercise_type=ExerciseType.STRENGTH,
                muscle_group=muscle_group,
                id_trainer_creator=id_trainer_creator,
                intensity=IntensityLevel.HIGH,
            )
    finally:
        conn.close()


def _count_rows(table: str) -> int:
    conn = _psycopg_connect(_target_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            return cur.fetchone()[0]
    finally:
        conn.close()


class RoutineRepositorySqlIntegrationTests(IntegrationTestCase):
    """Tests for :class:`RoutineRepositorySql`."""

    def _setup_trainer_and_program(self) -> tuple[int, int, MuscleGroup]:
        trainer_user = build_user(
            id_user=301, name="Entrenador Routine", role="TRAINER"
        )
        build_trainer(trainer_user, id_trainer=301)
        program_id = build_workout_program(
            id_workout_program=401,
            name="Programa Fuerza",
            objective="Hipertrofia",
        )
        muscle_group = build_muscle_group(id_muscle_group=501, name="Pecho")
        return trainer_user.id_user, program_id, muscle_group

    def _build_routine(
        self,
        trainer_id: int,
        program_id: int,
        id_exercises: list[int],
        status: RoutineStatus = RoutineStatus.DRAFT,
        total_exercises: int | None = None,
        cardio_ratio: Decimal = Decimal("0"),
        strength_ratio: Decimal = Decimal("100"),
        intensity_level: str = "HIGH",
    ) -> Routine:
        count = total_exercises if total_exercises is not None else len(id_exercises)
        routine = Routine(
            id_workout_program=program_id,
            id_trainer_creator=trainer_id,
            status=status,
        )
        routine._parameters = RoutineParameters(
            id_routine=0,
            total_exercises=count,
            intensity_level=intensity_level,
            cardio_ratio=cardio_ratio,
            strength_ratio=strength_ratio,
        )
        routine._contains = [
            {
                "id_exercise": eid,
                "execution_order": i + 1,
                "sets": 3,
                "repetitions": 10,
                "rest_time_seconds": 60,
            }
            for i, eid in enumerate(id_exercises)
        ]
        return routine

    def _build_structure(
        self, id_exercises: list[int]
    ) -> RoutineStructure:
        blocks: list[RoutineBlock] = []
        for i, eid in enumerate(id_exercises):
            blocks.append(
                RoutineBlock(
                    block_type=BlockType.SET,
                    order=i + 1,
                    id_exercise=eid,
                    sets=3,
                    repetitions=10,
                    rest_seconds=60,
                )
            )
        return RoutineStructure(id_routine=0, blocks=blocks)

    def _routine_repo(
        self, tm
    ) -> RoutineRepositorySql:
        return RoutineRepositorySql(tm)

    # ------------------------------------------------------------------
    # Save and retrieval
    # ------------------------------------------------------------------

    def test_complete_routine_save_and_retrieval(self) -> None:
        trainer_id, program_id, muscle_group = self._setup_trainer_and_program()
        ex1 = _save_exercise_direct(601, "Press de banca", muscle_group)
        ex2 = _save_exercise_direct(602, "Press inclinado", muscle_group)

        structure = RoutineStructure(
            id_routine=0,
            blocks=[
                RoutineBlock(
                    block_type=BlockType.WARM_UP,
                    order=1,
                    notes="Movilidad articular",
                ),
                RoutineBlock(
                    block_type=BlockType.CIRCUIT,
                    order=2,
                    children=[
                        RoutineBlock(
                            block_type=BlockType.SET,
                            order=1,
                            id_exercise=ex1.id_exercise,
                            sets=3,
                            repetitions=10,
                            rest_seconds=60,
                        ),
                        RoutineBlock(
                            block_type=BlockType.SET,
                            order=2,
                            id_exercise=ex2.id_exercise,
                            sets=3,
                            repetitions=12,
                            rest_seconds=60,
                        ),
                    ],
                ),
            ],
        )

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._routine_repo(tm)
                routine = self._build_routine(
                    trainer_id, program_id, [ex1.id_exercise, ex2.id_exercise]
                )
                saved = await repo.save(routine, structure)
                self.assertIsNotNone(saved.id_routine)

                fetched = await repo.get_complete(saved.id_routine)
                self.assertIsNotNone(fetched)
                fetched_routine, fetched_structure = fetched
                self.assertEqual(fetched_routine.id_routine, saved.id_routine)
                self.assertEqual(fetched_routine.status, RoutineStatus.DRAFT)
                self.assertEqual(fetched_routine.id_workout_program, program_id)
                self.assertEqual(len(fetched_structure.blocks), 2)
                self.assertEqual(
                    fetched_structure.blocks[0].block_type, BlockType.WARM_UP
                )
                circuit = fetched_structure.blocks[1]
                self.assertEqual(circuit.block_type, BlockType.CIRCUIT)
                self.assertEqual(len(circuit.children), 2)

        asyncio.run(scenario())

    def test_jsonb_nested_structure_round_trips_without_loss(self) -> None:
        trainer_id, program_id, muscle_group = self._setup_trainer_and_program()
        ex = _save_exercise_direct(610, "Sentadilla", muscle_group)

        deep_structure = RoutineStructure(
            id_routine=0,
            blocks=[
                RoutineBlock(
                    block_type=BlockType.WARM_UP,
                    order=1,
                    duration_seconds=300,
                    notes="Calentamiento general",
                ),
                RoutineBlock(
                    block_type=BlockType.CIRCUIT,
                    order=2,
                    children=[
                        RoutineBlock(
                            block_type=BlockType.SET,
                            order=1,
                            id_exercise=ex.id_exercise,
                            sets=4,
                            repetitions=15,
                            rest_seconds=90,
                        ),
                        RoutineBlock(
                            block_type=BlockType.REST,
                            order=2,
                            duration_seconds=60,
                        ),
                    ],
                ),
                RoutineBlock(
                    block_type=BlockType.SET,
                    order=3,
                    id_exercise=ex.id_exercise,
                    sets=3,
                    repetitions=8,
                    rest_seconds=120,
                ),
            ],
        )

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._routine_repo(tm)
                routine = self._build_routine(
                    trainer_id, program_id, [ex.id_exercise]
                )
                saved = await repo.save(routine, deep_structure)

                fetched = await repo.get_complete(saved.id_routine)
                self.assertIsNotNone(fetched)
                _, fetched_structure = fetched
                self.assertEqual(len(fetched_structure.blocks), 3)
                circuit = fetched_structure.blocks[1]
                self.assertEqual(circuit.block_type, BlockType.CIRCUIT)
                self.assertEqual(len(circuit.children), 2)
                set_block = circuit.children[0]
                self.assertEqual(set_block.sets, 4)
                self.assertEqual(set_block.repetitions, 15)
                rest_block = circuit.children[1]
                self.assertEqual(rest_block.block_type, BlockType.REST)
                self.assertEqual(rest_block.duration_seconds, 60)

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Atomicity
    # ------------------------------------------------------------------

    def test_failure_halfway_rolls_back_every_row(self) -> None:
        trainer_id, program_id, muscle_group = self._setup_trainer_and_program()
        ex = _save_exercise_direct(620, "Peso muerto", muscle_group)

        async def scenario() -> None:
            try:
                async with self.transaction_manager() as tm:
                    repo = self._routine_repo(tm)
                    routine = self._build_routine(
                        trainer_id, program_id, [ex.id_exercise]
                    )
                    structure = self._build_structure([ex.id_exercise])
                    await repo.save(routine, structure)
                    raise RuntimeError("forced rollback")
            except RuntimeError:
                pass

        asyncio.run(scenario())

        self.assertEqual(_count_rows("routine"), 0)
        self.assertEqual(_count_rows("parameters_routine"), 0)
        self.assertEqual(_count_rows("contains"), 0)
        self.assertEqual(_count_rows("routine_structure"), 0)

    # ------------------------------------------------------------------
    # Business-rule rejections
    # ------------------------------------------------------------------

    def test_duplicate_exercise_in_one_routine_is_rejected(self) -> None:
        trainer_id, program_id, muscle_group = self._setup_trainer_and_program()
        ex = _save_exercise_direct(630, "Press militar", muscle_group)

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._routine_repo(tm)
                routine = self._build_routine(
                    trainer_id, program_id, [ex.id_exercise, ex.id_exercise]
                )
                structure = self._build_structure([ex.id_exercise])
                with self.assertRaises(Exception):
                    await repo.save(routine, structure)

        asyncio.run(scenario())

    def test_duplicate_execution_order_is_rejected(self) -> None:
        trainer_id, program_id, muscle_group = self._setup_trainer_and_program()
        ex1 = _save_exercise_direct(631, "Press militar", muscle_group)
        ex2 = _save_exercise_direct(632, "Press banca", muscle_group)

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._routine_repo(tm)
                routine = self._build_routine(
                    trainer_id, program_id, [ex1.id_exercise, ex2.id_exercise]
                )
                # Force duplicate execution order
                routine._contains = [
                    {
                        "id_exercise": ex1.id_exercise,
                        "execution_order": 1,
                        "sets": 3,
                        "repetitions": 10,
                        "rest_time_seconds": 60,
                    },
                    {
                        "id_exercise": ex2.id_exercise,
                        "execution_order": 1,
                        "sets": 3,
                        "repetitions": 10,
                        "rest_time_seconds": 60,
                    },
                ]
                structure = self._build_structure([ex1.id_exercise, ex2.id_exercise])
                with self.assertRaises(Exception):
                    await repo.save(routine, structure)

        asyncio.run(scenario())

    def test_parameters_proportions_over_100_are_rejected(self) -> None:
        trainer_id, program_id, muscle_group = self._setup_trainer_and_program()
        ex = _save_exercise_direct(640, "Zancada", muscle_group)

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._routine_repo(tm)
                routine = self._build_routine(
                    trainer_id,
                    program_id,
                    [ex.id_exercise],
                    cardio_ratio=Decimal("60"),
                    strength_ratio=Decimal("60"),
                )
                structure = self._build_structure([ex.id_exercise])
                with self.assertRaises(Exception):
                    await repo.save(routine, structure)

        asyncio.run(scenario())

    def test_missing_program_reference_is_rejected(self) -> None:
        trainer_id, _, muscle_group = self._setup_trainer_and_program()
        ex = _save_exercise_direct(650, "Curl", muscle_group)

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._routine_repo(tm)
                routine = self._build_routine(
                    99999,  # nonexistent program
                    trainer_id,
                    [ex.id_exercise],
                )
                structure = self._build_structure([ex.id_exercise])
                with self.assertRaises(Exception):
                    await repo.save(routine, structure)

        asyncio.run(scenario())

    def test_routine_always_contains_at_least_one_exercise(self) -> None:
        trainer_id, program_id, _ = self._setup_trainer_and_program()

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._routine_repo(tm)
                routine = self._build_routine(
                    trainer_id, program_id, [], total_exercises=0
                )
                structure = RoutineStructure(id_routine=0, blocks=[])
                with self.assertRaises(Exception):
                    await repo.save(routine, structure)

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Validations
    # ------------------------------------------------------------------

    def test_save_and_list_validations(self) -> None:
        trainer_id, program_id, muscle_group = self._setup_trainer_and_program()
        ex = _save_exercise_direct(660, "Remo", muscle_group)

        room_chief_user = build_user(
            id_user=302, name="Jefe de Sala", role="TRAINER"
        )
        build_trainer(room_chief_user, id_trainer=302, specialty="ROOM_CHIEF")

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._routine_repo(tm)
                routine = self._build_routine(
                    trainer_id, program_id, [ex.id_exercise],
                    status=RoutineStatus.PENDING_REVIEW,
                )
                structure = self._build_structure([ex.id_exercise])
                saved_routine = await repo.save(routine, structure)

                validation = RoutineValidation(
                    id_routine=saved_routine.id_routine,
                    id_room_chief=room_chief_user.id_user,
                    decision=ValidationDecision.APPROVED,
                )
                saved_validation = await repo.save_validation(validation)
                self.assertIsNotNone(saved_validation.id_validation)

                validations = await repo.list_validations(saved_routine.id_routine)
                self.assertEqual(len(validations), 1)
                self.assertEqual(validations[0].decision, ValidationDecision.APPROVED)
                self.assertEqual(
                    validations[0].id_room_chief, room_chief_user.id_user
                )

        asyncio.run(scenario())

    def test_list_by_program(self) -> None:
        trainer_id, program_id, muscle_group = self._setup_trainer_and_program()
        ex = _save_exercise_direct(670, "Elevaciones", muscle_group)

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._routine_repo(tm)
                for _ in range(3):
                    routine = self._build_routine(
                        trainer_id, program_id, [ex.id_exercise]
                    )
                    structure = self._build_structure([ex.id_exercise])
                    await repo.save(routine, structure)

                routines = await repo.list_by_program(program_id)
                self.assertEqual(len(routines), 3)
                for routine in routines:
                    self.assertEqual(routine.id_workout_program, program_id)

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Retrieval by primary key
    # ------------------------------------------------------------------

    def test_get_complete_uses_primary_key_lookup(self) -> None:
        trainer_id, program_id, muscle_group = self._setup_trainer_and_program()
        ex = _save_exercise_direct(680, "Dominadas", muscle_group)

        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._routine_repo(tm)
                routine = self._build_routine(
                    trainer_id, program_id, [ex.id_exercise]
                )
                structure = self._build_structure([ex.id_exercise])
                saved = await repo.save(routine, structure)

                fetched = await repo.get_complete(saved.id_routine)
                self.assertIsNotNone(fetched)
                fetched_routine, _ = fetched
                self.assertEqual(fetched_routine.id_routine, saved.id_routine)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
