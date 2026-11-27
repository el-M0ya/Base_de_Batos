"""Integration tests for routine review API (issue E6-04).

Covers HTTP -> application -> PostgreSQL with real transaction management:
listing pending reviews, approving, rejecting, missing observations,
nonexistent routines, missing authorization, and invalid transitions.
"""

from __future__ import annotations

import asyncio
import unittest
from contextlib import AsyncExitStack
from datetime import date
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
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence.transaction import PsqlTransactionManager
from app.main import app

import psycopg


REVIEWER_ID = 2001
OTHER_TRAINER_ID = 2002
PROGRAM_ID = 601
OTHER_PROGRAM_ID = 602
REVIEW_DATE = date(2026, 6, 1)


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


class RoutineReviewsApiIntegrationTests(IntegrationTestCase):
    """HTTP -> application -> PostgreSQL tests for routine review endpoints."""

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
        self._install_overrides(
            ActorDTO(id_user=REVIEWER_ID, role=UserRole.TRAINER)
        )

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    # ------------------------------------------------------------------
    # Seeding
    # ------------------------------------------------------------------

    def _seed_common_data(self) -> None:
        """Insert reviewers, programs, authorisations, catalogs, exercises."""
        build_muscle_group(id_muscle_group=3, name="Legs")
        build_workout_program(
            id_workout_program=PROGRAM_ID,
            name="Leg Day",
            objective="Lower body",
        )
        build_workout_program(
            id_workout_program=OTHER_PROGRAM_ID,
            name="Other Program",
            objective="Other",
        )
        for trainer_id, program_id, can_validate in (
            (REVIEWER_ID, PROGRAM_ID, True),
            (REVIEWER_ID, OTHER_PROGRAM_ID, False),
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
                ) VALUES (%s, %s, FALSE, %s, %s, NULL)
                """,
                (trainer_id, program_id, can_validate, date(2026, 1, 1)),
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
        _execute(
            """
            INSERT INTO exercise (
                name, description, registration_date,
                id_exercise_type, id_muscle_group, id_trainer_creator, intensity
            ) VALUES (
                'Squat', 'Lower body exercise', %s,
                (SELECT id_exercise_type FROM exercise_type WHERE name = 'fuerza'),
                3, %s,
                (SELECT id_intensity_level FROM intensity_level WHERE name = 'alto')
            )
            """,
            (REVIEW_DATE, REVIEWER_ID),
        )

    def _seed_pending_routine(
        self, id_routine: int, id_trainer_creator: int, id_workout_program: int
    ) -> None:
        """Insert a routine directly in PENDING_REVIEW status for review tests."""
        _execute(
            """
            INSERT INTO routine (
                id_routine, status, creation_date,
                id_workout_program, id_trainer_creator, id_client, id_routine_origin
            ) VALUES (%s, %s, %s, %s, %s, NULL, NULL)
            """,
            (
                id_routine,
                "PENDING_REVIEW",
                REVIEW_DATE,
                id_workout_program,
                id_trainer_creator,
            ),
        )
        _execute(
            """
            INSERT INTO parameters_routine (
                id_routine, total_exercises, intensity_level,
                cardio_ratio, strength_ratio, flexibility_ratio,
                covered_muscle_group_ids
            ) VALUES (%s, 1, 'ALTO', 0.00, 100.00, 0.00, ARRAY[3])
            """,
            (id_routine,),
        )
        _execute(
            """
            INSERT INTO contains (
                id_routine, id_exercise, execution_order,
                sets, repetitions, rest_time_seconds
            ) VALUES (%s, 1, 1, 3, 10, 60)
            """,
            (id_routine,),
        )
        _execute(
            """
            INSERT INTO routine_structure (id_routine, structure_json)
            VALUES (%s, '{"blocks": []}')
            """,
            (id_routine,),
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

    def _post_review(
        self,
        id_routine: int,
        decision: str,
        observations: Optional[str] = None,
        validation_date: Optional[str] = None,
        *,
        token: str | None = None,
    ):
        payload: dict = {"decision": decision}
        if observations is not None:
            payload["observations"] = observations
        if validation_date is not None:
            payload["validation_date"] = validation_date
        headers = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        return self.client.post(
            f"/api/v1/routines/{id_routine}/review",
            json=payload,
            headers=headers,
        )

    def _get_pending_reviews(self, *, token: str | None = None):
        headers = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        return self.client.get("/api/v1/routines/pending-review", headers=headers)

    # ------------------------------------------------------------------
    # List pending reviews
    # ------------------------------------------------------------------

    def test_list_pending_reviews_returns_only_pending_and_authorized(self) -> None:
        """Reviewer sees only PENDING_REVIEW routines from authorized programs."""
        # Routine 1: PENDING_REVIEW in PROGRAM_ID (reviewer has can_validate)
        self._seed_pending_routine(1, REVIEWER_ID, PROGRAM_ID)
        # Routine 2: APPROVED in PROGRAM_ID (should not appear)
        _execute(
            """
            INSERT INTO routine (
                id_routine, status, creation_date,
                id_workout_program, id_trainer_creator, id_client, id_routine_origin
            ) VALUES (2, 'APPROVED', %s, %s, %s, NULL, NULL)
            """,
            (REVIEW_DATE, PROGRAM_ID, REVIEWER_ID),
        )
        # Routine 3: PENDING_REVIEW in OTHER_PROGRAM_ID (reviewer has NO can_validate)
        self._seed_pending_routine(3, REVIEWER_ID, OTHER_PROGRAM_ID)

        response = self._get_pending_reviews()
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["id_routine"], 1)
        self.assertEqual(body[0]["id_workout_program"], PROGRAM_ID)
        self.assertEqual(body[0]["status"], "PENDING_REVIEW")

    def test_list_pending_reviews_empty_when_no_authorization(self) -> None:
        """Reviewer with no can_validate anywhere sees empty list."""
        self._seed_pending_routine(1, REVIEWER_ID, PROGRAM_ID)
        # Remove the reviewer's can_validate for PROGRAM_ID
        _execute(
            """
            UPDATE authorises SET can_validate = FALSE
            WHERE id_trainer = %s AND id_workout_program = %s
            """,
            (REVIEWER_ID, PROGRAM_ID),
        )
        try:
            response = self._get_pending_reviews()
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), [])
        finally:
            _execute(
                """
                UPDATE authorises SET can_validate = TRUE
                WHERE id_trainer = %s AND id_workout_program = %s
                """,
                (REVIEWER_ID, PROGRAM_ID),
            )

    # ------------------------------------------------------------------
    # Approve
    # ------------------------------------------------------------------

    def test_approve_pending_routine_returns_updated_status(self) -> None:
        """Approving a PENDING_REVIEW routine returns APPROVED status."""
        self._seed_pending_routine(1, REVIEWER_ID, PROGRAM_ID)
        response = self._post_review(1, "APPROVED")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["id_routine"], 1)
        self.assertEqual(body["decision"], "APPROVED")
        self.assertEqual(body["routine_status"], "APPROVED")
        self.assertEqual(body["id_room_chief"], REVIEWER_ID)

        # Verify persisted status
        row = _fetch_one(
            "SELECT status FROM routine WHERE id_routine = %s",
            (1,),
        )
        self.assertEqual(row[0], "APPROVED")

    def test_reject_pending_routine_with_observations(self) -> None:
        """Rejecting with observations returns REJECTED status."""
        self._seed_pending_routine(1, REVIEWER_ID, PROGRAM_ID)
        response = self._post_review(
            1, "REJECTED", observations="Needs more cardio."
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["decision"], "REJECTED")
        self.assertEqual(body["routine_status"], "REJECTED")
        self.assertEqual(body["observations"], "Needs more cardio.")

        row = _fetch_one(
            "SELECT status FROM routine WHERE id_routine = %s",
            (1,),
        )
        self.assertEqual(row[0], "REJECTED")

    # ------------------------------------------------------------------
    # Error cases
    # ------------------------------------------------------------------

    def test_reject_without_observations_returns_422(self) -> None:
        """A rejection without observations is rejected."""
        self._seed_pending_routine(1, REVIEWER_ID, PROGRAM_ID)
        response = self._post_review(1, "REJECTED")
        self.assertEqual(response.status_code, 422, response.text)
        body = response.json()
        self.assertEqual(body["code"], "INVALID_INPUT")

        # Status must remain unchanged
        row = _fetch_one(
            "SELECT status FROM routine WHERE id_routine = %s",
            (1,),
        )
        self.assertEqual(row[0], "PENDING_REVIEW")

    def test_review_nonexistent_routine_returns_404(self) -> None:
        """Reviewing a nonexistent routine returns RESOURCE_NOT_FOUND."""
        response = self._post_review(999999, "APPROVED")
        self.assertEqual(response.status_code, 404, response.text)
        body = response.json()
        self.assertEqual(body["code"], "RESOURCE_NOT_FOUND")

    def test_review_without_can_validate_returns_403(self) -> None:
        """Trainer without can_validate for the program gets PERMISSION_DENIED."""
        # Reviewer has can_validate on PROGRAM_ID; use OTHER_TRAINER_ID who
        # has can_validate on PROGRAM_ID too but switch to a trainer without it.
        # Simpler: seed a routine in OTHER_PROGRAM_ID where reviewer has NO can_validate.
        self._seed_pending_routine(1, REVIEWER_ID, OTHER_PROGRAM_ID)
        response = self._post_review(1, "APPROVED")
        self.assertEqual(response.status_code, 403, response.text)
        body = response.json()
        self.assertEqual(body["code"], "PERMISSION_DENIED")

    def test_review_non_trainer_actor_returns_403(self) -> None:
        """A client actor cannot review routines."""
        self._install_overrides(
            ActorDTO(id_user=REVIEWER_ID, role=UserRole.CLIENT)
        )
        try:
            self._seed_pending_routine(1, REVIEWER_ID, PROGRAM_ID)
            response = self._post_review(1, "APPROVED")
            self.assertEqual(response.status_code, 403, response.text)
            body = response.json()
            self.assertEqual(body["code"], "PERMISSION_DENIED")
        finally:
            self._install_overrides(
                ActorDTO(id_user=REVIEWER_ID, role=UserRole.TRAINER)
            )

    def test_approve_already_approved_routine_returns_422(self) -> None:
        """Approving an already APPROVED routine is an invalid transition."""
        _execute(
            """
            INSERT INTO routine (
                id_routine, status, creation_date,
                id_workout_program, id_trainer_creator, id_client, id_routine_origin
            ) VALUES (1, 'APPROVED', %s, %s, %s, NULL, NULL)
            """,
            (REVIEW_DATE, PROGRAM_ID, REVIEWER_ID),
        )
        response = self._post_review(1, "APPROVED")
        self.assertEqual(response.status_code, 422, response.text)
        body = response.json()
        self.assertEqual(body["code"], "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
