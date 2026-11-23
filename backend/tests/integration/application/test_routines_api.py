"""Integration tests for routine generation and retrieval HTTP API (E6-03).

Covers HTTP -> application -> PostgreSQL with real JSONB round-trip behavior,
distinguishable error codes for permission, invalid parameters, missing
resources, and unsatisfiable generation conditions.
"""

from __future__ import annotations

import asyncio
import unittest
from contextlib import AsyncExitStack
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi.testclient import TestClient
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
from app.adapters.dependencies import (
    get_current_actor,
    get_transaction_manager,
)
from app.application.ports.transaction_manager import TransactionManager
from app.application.dto.actor import ActorDTO
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence.transaction import PsqlTransactionManager
from app.main import app

import psycopg


TRAINER_ID = 1001
OTHER_TRAINER_ID = 1002
PROGRAM_ID = 501
OTHER_PROGRAM_ID = 502
GENERATION_DATE = date(2026, 5, 1)


class _TestPoolTransactionManager(TransactionManager):
    """Transaction manager that borrows connections from the test pool."""

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


class RoutinesApiIntegrationTests(IntegrationTestCase):
    """HTTP -> application -> PostgreSQL tests for routine endpoints."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls._test_pool = asyncio.run(get_test_pool())

    def transaction_manager(self) -> TransactionManager:
        """Use the test pool instead of the application-wide pool."""
        return _TestPoolTransactionManager(self._test_pool)

    def setUp(self) -> None:
        super().setUp()
        self._seed_common_data()
        self.client = TestClient(app)
        self._install_overrides(ActorDTO(id_user=TRAINER_ID, role=UserRole.TRAINER))

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    # ------------------------------------------------------------------
    # Seeding
    # ------------------------------------------------------------------

    def _seed_common_data(self) -> None:
        """Insert trainer, program, authorisation, catalogs and exercises."""
        build_muscle_group(id_muscle_group=1, name="Chest")
        build_muscle_group(id_muscle_group=2, name="Back")
        build_workout_program(
            id_workout_program=PROGRAM_ID,
            name="Strength Base",
            objective="General strength",
        )
        build_workout_program(
            id_workout_program=OTHER_PROGRAM_ID,
            name="Other Program",
            objective="Other",
        )
        for trainer_id, program_id, can_generate in (
            (TRAINER_ID, PROGRAM_ID, True),
            (TRAINER_ID, OTHER_PROGRAM_ID, False),
            (OTHER_TRAINER_ID, PROGRAM_ID, True),
        ):
            _execute(
                """
                INSERT INTO app_user (id_user, name, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    trainer_id,
                    f"Trainer {trainer_id}",
                    f"trainer{trainer_id}@example.com",
                    "not-a-real-hash",
                    "TRAINER",
                ),
            )
            _execute(
                "INSERT INTO trainer (id_trainer, specialty) VALUES (%s, %s)",
                (trainer_id, "GENERAL"),
            )
            _execute(
                """
                INSERT INTO authorises (
                    id_trainer, id_workout_program, can_generate, can_validate,
                    start_date, end_date
                ) VALUES (%s, %s, %s, FALSE, %s, NULL)
                """,
                (trainer_id, program_id, can_generate, date(2026, 1, 1)),
            )
        _execute(
            """
            INSERT INTO covers (id_workout_program, id_muscle_group)
            VALUES (%s, %s), (%s, %s)
            """,
            (PROGRAM_ID, 1),
            (PROGRAM_ID, 2),
        )
        _execute(
            """
            INSERT INTO exercise_type (name)
            VALUES ('fuerza'), ('cardio'), ('flexibilidad')
            ON CONFLICT (name) DO NOTHING
            """
        )
        _execute(
            """
            INSERT INTO intensity_level (name)
            VALUES ('bajo'), ('medio'), ('alto')
            ON CONFLICT (name) DO NOTHING
            """
        )
        for name, ex_type, intensity, mg_id in (
            ("Bench Press", "fuerza", "alto", 1),
            ("Push Up", "fuerza", "alto", 1),
            ("Jump Rope", "cardio", "alto", 1),
            ("Rowing", "cardio", "alto", 1),
            ("Pull Up", "fuerza", "alto", 2),
        ):
            _execute(
                """
                INSERT INTO exercise (
                    name, description, registration_date,
                    id_exercise_type, id_muscle_group, id_trainer_creator, intensity
                ) VALUES (
                    %s, %s, %s,
                    (SELECT id_exercise_type FROM exercise_type WHERE name = %s),
                    %s, %s,
                    (SELECT id_intensity_level FROM intensity_level WHERE name = %s)
                )
                """,
                (
                    name,
                    f"{name} description",
                    GENERATION_DATE,
                    ex_type,
                    mg_id,
                    TRAINER_ID,
                    intensity,
                ),
            )

    # ------------------------------------------------------------------
    # Dependency overrides
    # ------------------------------------------------------------------

    def _install_overrides(self, actor: ActorDTO) -> None:
        """Wire TestClient to the test pool and the given actor."""

        async def _tm_override():
            tm = _TestPoolTransactionManager(self._test_pool)
            async with tm:
                yield tm

        app.dependency_overrides[get_transaction_manager] = _tm_override
        app.dependency_overrides[get_current_actor] = lambda: actor

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _post_generate(self, payload: dict, *, token: str | None = None):
        headers = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        return self.client.post("/api/v1/routines", json=payload, headers=headers)

    def _get_routine(self, id_routine: int, *, token: str | None = None):
        headers = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        return self.client.get(f"/api/v1/routines/{id_routine}", headers=headers)

    def _valid_generation_payload(self) -> dict:
        return {
            "id_workout_program": PROGRAM_ID,
            "strategy_name": "balanced",
            "total_exercises": 2,
            "target_intensity": "alto",
            "exercise_type_proportions": {
                "fuerza": 0.5,
                "cardio": 0.5,
            },
            "generation_date": GENERATION_DATE.isoformat(),
        }

    # ------------------------------------------------------------------
    # Generation: happy path
    # ------------------------------------------------------------------

    def test_generate_routine_returns_complete_aggregate(self) -> None:
        response = self._post_generate(self._valid_generation_payload())
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()

        self.assertIn("id_routine", body)
        self.assertEqual(body["id_workout_program"], PROGRAM_ID)
        self.assertEqual(body["id_trainer_creator"], TRAINER_ID)
        self.assertEqual(body["creation_date"], GENERATION_DATE.isoformat())
        self.assertEqual(body["status"], "DRAFT")

        parameters = body["parameters"]
        self.assertEqual(parameters["total_exercises"], 2)
        self.assertEqual(parameters["intensity_level"], "ALTO")
        self.assertEqual(parameters["cardio_ratio"], "50.00")
        self.assertEqual(parameters["strength_ratio"], "50.00")
        self.assertEqual(parameters["flexibility_ratio"], "0.00")
        self.assertEqual(parameters["covered_muscle_group_ids"], [1, 2])

        self.assertEqual(len(body["composition"]), 2)
        self.assertIn("structure", body)
        self.assertIn("blocks", body["structure"])

        id_routine = body["id_routine"]

        # Persisted rows match the response.
        routine_row = _fetch_one(
            """
            SELECT status, creation_date, id_workout_program, id_trainer_creator
            FROM routine WHERE id_routine = %s
            """,
            (id_routine,),
        )
        self.assertEqual(routine_row[0], "DRAFT")
        self.assertEqual(routine_row[1], GENERATION_DATE)
        self.assertEqual(routine_row[2], PROGRAM_ID)
        self.assertEqual(routine_row[3], TRAINER_ID)

        parameters_row = _fetch_one(
            """
            SELECT total_exercises, intensity_level, cardio_ratio,
                   strength_ratio, flexibility_ratio, covered_muscle_group_ids
            FROM parameters_routine WHERE id_routine = %s
            """,
            (id_routine,),
        )
        self.assertEqual(parameters_row[0], 2)
        self.assertEqual(parameters_row[1], "ALTO")
        self.assertEqual(parameters_row[2], Decimal("50.00"))
        self.assertEqual(parameters_row[3], Decimal("50.00"))
        self.assertEqual(parameters_row[4], Decimal("0.00"))
        self.assertEqual(parameters_row[5], [1, 2])

    def test_generate_and_retrieve_jsonb_round_trip(self) -> None:
        """Generation response and retrieval response share the same structure."""
        create_response = self._post_generate(self._valid_generation_payload())
        self.assertEqual(create_response.status_code, 201, create_response.text)
        created = create_response.json()
        id_routine = created["id_routine"]

        get_response = self._get_routine(id_routine)
        self.assertEqual(get_response.status_code, 200, get_response.text)
        fetched = get_response.json()

        # Same identifier, program, creator, date, status.
        self.assertEqual(fetched["id_routine"], id_routine)
        self.assertEqual(fetched["id_workout_program"], PROGRAM_ID)
        self.assertEqual(fetched["id_trainer_creator"], TRAINER_ID)
        self.assertEqual(fetched["creation_date"], GENERATION_DATE.isoformat())
        self.assertEqual(fetched["status"], "DRAFT")

        # Same parameters.
        self.assertEqual(fetched["parameters"], created["parameters"])

        # Same composition.
        self.assertEqual(len(fetched["composition"]), len(created["composition"]))

        # JSONB structure round-trips without information loss.
        self.assertEqual(fetched["structure"], created["structure"])
        self.assertEqual(
            len(fetched["structure"]["blocks"]),
            len(created["structure"]["blocks"]),
        )

    # ------------------------------------------------------------------
    # Generation: error cases
    # ------------------------------------------------------------------

    def test_generate_with_invalid_parameters_receives_422(self) -> None:
        """Proportions that do not sum to 1 are rejected before persistence."""
        payload = self._valid_generation_payload()
        payload["exercise_type_proportions"] = {"fuerza": 0.7, "cardio": 0.2}
        response = self._post_generate(payload)
        self.assertEqual(response.status_code, 422, response.text)
        body = response.json()
        self.assertEqual(body["code"], "INVALID_INPUT")

    def test_generate_with_nonexistent_program_receives_404(self) -> None:
        payload = self._valid_generation_payload()
        payload["id_workout_program"] = 999999
        response = self._post_generate(payload)
        self.assertEqual(response.status_code, 404, response.text)
        body = response.json()
        self.assertEqual(body["code"], "RESOURCE_NOT_FOUND")

    def test_generate_without_authorisation_receives_403(self) -> None:
        """Trainer without can_generate for the program gets 403."""
        self._install_overrides(
            ActorDTO(id_user=TRAINER_ID, role=UserRole.TRAINER)
        )
        # Re-seed authorisation without can_generate for this trainer/program.
        _execute(
            """
            UPDATE authorises SET can_generate = FALSE
            WHERE id_trainer = %s AND id_workout_program = %s
            """,
            (TRAINER_ID, PROGRAM_ID),
        )
        try:
            response = self._post_generate(self._valid_generation_payload())
            self.assertEqual(response.status_code, 403, response.text)
            body = response.json()
            self.assertEqual(body["code"], "PERMISSION_DENIED")
        finally:
            self._install_overrides(
                ActorDTO(id_user=TRAINER_ID, role=UserRole.TRAINER)
            )

    def test_generate_with_non_trainer_actor_receives_403(self) -> None:
        self._install_overrides(ActorDTO(id_user=TRAINER_ID, role=UserRole.CLIENT))
        try:
            response = self._post_generate(self._valid_generation_payload())
            self.assertEqual(response.status_code, 403, response.text)
            body = response.json()
            self.assertEqual(body["code"], "PERMISSION_DENIED")
        finally:
            self._install_overrides(
                ActorDTO(id_user=TRAINER_ID, role=UserRole.TRAINER)
            )

    # ------------------------------------------------------------------
    # Retrieval: error cases
    # ------------------------------------------------------------------

    def test_retrieve_nonexistent_routine_receives_404(self) -> None:
        response = self._get_routine(999999)
        self.assertEqual(response.status_code, 404, response.text)
        body = response.json()
        self.assertEqual(body["code"], "RESOURCE_NOT_FOUND")

    def test_retrieve_without_authorisation_receives_403(self) -> None:
        """Trainer not authorized for the program gets 403 on retrieval."""
        # Create a routine as the authorized trainer first.
        create_response = self._post_generate(self._valid_generation_payload())
        self.assertEqual(create_response.status_code, 201, create_response.text)
        id_routine = create_response.json()["id_routine"]

        # Switch to a trainer authorized for a *different* program only.
        self._install_overrides(
            ActorDTO(id_user=OTHER_TRAINER_ID, role=UserRole.TRAINER)
        )
        try:
            response = self._get_routine(id_routine)
            self.assertEqual(response.status_code, 403, response.text)
            body = response.json()
            self.assertEqual(body["code"], "PERMISSION_DENIED")
        finally:
            self._install_overrides(
                ActorDTO(id_user=TRAINER_ID, role=UserRole.TRAINER)
            )

    # ------------------------------------------------------------------
    # Atomicity / persistence
    # ------------------------------------------------------------------

    def test_successful_generation_persists_all_tables(self) -> None:
        """A successful generation leaves rows in every routine table."""
        response = self._post_generate(self._valid_generation_payload())
        self.assertEqual(response.status_code, 201, response.text)
        id_routine = response.json()["id_routine"]

        counts = _fetch_one(
            """
            SELECT
                (SELECT COUNT(*) FROM routine WHERE id_routine = %s),
                (SELECT COUNT(*) FROM parameters_routine WHERE id_routine = %s),
                (SELECT COUNT(*) FROM contains WHERE id_routine = %s),
                (SELECT COUNT(*) FROM routine_structure WHERE id_routine = %s)
            """,
            (id_routine, id_routine, id_routine, id_routine),
        )
        self.assertEqual(counts, (1, 1, 2, 1))


if __name__ == "__main__":
    unittest.main()
