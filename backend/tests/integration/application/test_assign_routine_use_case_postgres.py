"""Integration tests for assigning a routine to a client against PostgreSQL.

The tests use the real SQL repositories inside one ``PsqlTransactionManager``
block. They cover the persisted assignment dates, RF-28 validation failures,
the U-9 duplicate guard, and rollback of the assignment write.
"""

from __future__ import annotations

import asyncio
import unittest
from datetime import date

import psycopg

from backend.tests.integration.base import IntegrationTestCase
from backend.tests.integration.support.builders import (
    build_client,
    build_site,
    build_trainer,
    build_user,
    build_workout_program,
)
from backend.tests.integration.support.database import _target_db_dsn
from app.application.dto.routine_assignment_dto import AssignRoutineInputDTO
from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.application.use_cases.assign_routine import AssignRoutineUseCase
from app.domain.entities.enrolment import Enrolment
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence.repositories.assignment_repository_sql import (
    AssignmentRepositorySql,
)
from app.infrastructure.persistence.repositories.enrolment_repository_sql import (
    EnrolmentRepositorySql,
)
from app.infrastructure.persistence.repositories.routine_repository_sql import (
    RoutineRepositorySql,
)


CLIENT_ID = 903
TRAINER_ID = 902
PROGRAM_ID = 904
ROUTINE_ID = 905
START_DATE = date(2026, 2, 1)
END_DATE = date(2026, 4, 30)


def _create_routine_direct() -> None:
    """Insert a routine header with the minimal complete structure."""
    conn = psycopg.connect(_target_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO routine (id_routine, status, creation_date,
                    id_workout_program, id_trainer_creator)
                VALUES (%s, 'DRAFT', %s, %s, %s)
                """,
                (ROUTINE_ID, date(2026, 1, 1), PROGRAM_ID, TRAINER_ID),
            )
            cur.execute(
                """
                INSERT INTO parameters_routine (id_routine, total_exercises,
                    intensity_level, cardio_ratio, strength_ratio)
                VALUES (%s, 1, 'MEDIUM', 0, 100)
                """,
                (ROUTINE_ID,),
            )
            cur.execute(
                """
                INSERT INTO routine_structure (id_routine, structure_json)
                VALUES (%s, %s::jsonb)
                """,
                (ROUTINE_ID, '{"blocks": []}'),
            )
    finally:
        conn.close()


def _assignment_count() -> int:
    """Return the number of stored assignments."""
    conn = psycopg.connect(_target_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM assignment")
            return int(cur.fetchone()[0])
    finally:
        conn.close()


class AssignRoutineUseCaseIntegrationTests(IntegrationTestCase):
    """Persistence and business-rule tests for routine assignment."""

    def setUp(self) -> None:
        super().setUp()
        self.site = build_site(id_site=901)
        trainer = build_user(
            id_user=TRAINER_ID,
            name="Trainer",
            email="trainer.assignment@ejemplo.com",
            role=UserRole.TRAINER,
        )
        build_trainer(trainer, id_trainer=TRAINER_ID)
        client = build_user(
            id_user=CLIENT_ID,
            name="Client",
            email="client.assignment@ejemplo.com",
            role=UserRole.CLIENT,
        )
        build_client(
            client, id_client=CLIENT_ID, id_site=self.site.id_site
        )
        build_workout_program(id_workout_program=PROGRAM_ID)
        _create_routine_direct()

    def _input(self, **overrides) -> AssignRoutineInputDTO:
        values = {
            "id_routine": ROUTINE_ID,
            "id_client": CLIENT_ID,
            "assignment_date": START_DATE,
            "end_date": END_DATE,
        }
        values.update(overrides)
        return AssignRoutineInputDTO(**values)

    async def _execute(self, *inputs: AssignRoutineInputDTO, enrol: bool = True):
        """Run the use case with real repositories over one transaction."""
        results = []
        async with self.transaction_manager() as tm:
            routines = RoutineRepositorySql(tm)
            connection = tm.connection()
            enrolments = EnrolmentRepositorySql(connection)
            assignments = AssignmentRepositorySql(tm)
            if enrol:
                await enrolments.create(
                    Enrolment(
                        id_client=CLIENT_ID,
                        id_workout_program=PROGRAM_ID,
                        enrollment_date=date(2026, 1, 15),
                    )
                )
            use_case = AssignRoutineUseCase(
                routines, enrolments, assignments
            )
            for input_dto in inputs:
                results.append(await use_case.execute(input_dto))
        return results

    def test_assigns_routine_and_persists_dates(self) -> None:
        async def scenario() -> None:
            results = await self._execute(self._input())

            self.assertEqual(1, len(results))
            self.assertEqual(1, results[0].id_assignment)
            self.assertEqual(ROUTINE_ID, results[0].id_routine)
            self.assertEqual(CLIENT_ID, results[0].id_client)
            self.assertEqual(START_DATE, results[0].assignment_date)
            self.assertEqual(END_DATE, results[0].end_date)

        asyncio.run(scenario())

        conn = psycopg.connect(_target_db_dsn(), autocommit=True)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id_routine, id_client, fecha_asignacion, fecha_fin
                    FROM assignment
                    """
                )
                self.assertEqual(
                    [(ROUTINE_ID, CLIENT_ID, START_DATE, END_DATE)],
                    cur.fetchall(),
                )
        finally:
            conn.close()

    def test_rejects_assignment_without_enrollment(self) -> None:
        async def scenario() -> None:
            with self.assertRaises(BusinessRuleViolation):
                await self._execute(self._input(), enrol=False)

        asyncio.run(scenario())
        self.assertEqual(0, _assignment_count())

    def test_rejects_unknown_routine_and_client(self) -> None:
        async def scenario() -> None:
            with self.assertRaises(ResourceNotFound):
                await self._execute(self._input(id_routine=999999))
            with self.assertRaises(ResourceNotFound):
                await self._execute(self._input(id_client=999999))

        asyncio.run(scenario())
        self.assertEqual(0, _assignment_count())

    def test_rejects_duplicate_assignment(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                routines = RoutineRepositorySql(tm)
                connection = tm.connection()
                enrolments = EnrolmentRepositorySql(connection)
                assignments = AssignmentRepositorySql(tm)
                await enrolments.create(
                    Enrolment(
                        id_client=CLIENT_ID,
                        id_workout_program=PROGRAM_ID,
                        enrollment_date=date(2026, 1, 15),
                    )
                )
                use_case = AssignRoutineUseCase(
                    routines, enrolments, assignments
                )
                await use_case.execute(self._input())
                with self.assertRaises(DuplicateResource):
                    await use_case.execute(self._input())

        asyncio.run(scenario())
        self.assertEqual(1, _assignment_count())

    def test_rejects_end_date_before_start_date(self) -> None:
        async def scenario() -> None:
            with self.assertRaises(InvalidInput):
                await self._execute(
                    self._input(end_date=date(2026, 1, 31))
                )

        asyncio.run(scenario())
        self.assertEqual(0, _assignment_count())

    def test_assignment_write_rolls_back_with_transaction(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                routines = RoutineRepositorySql(tm)
                connection = tm.connection()
                enrolments = EnrolmentRepositorySql(connection)
                assignments = AssignmentRepositorySql(tm)
                await enrolments.create(
                    Enrolment(
                        id_client=CLIENT_ID,
                        id_workout_program=PROGRAM_ID,
                        enrollment_date=date(2026, 1, 15),
                    )
                )
                use_case = AssignRoutineUseCase(
                    routines, enrolments, assignments
                )
                await use_case.execute(self._input())

                # A later failure in the same unit of work must undo the
                # assignment inserted by the use case.
                await connection.execute(
                    """
                    INSERT INTO assignment (id_routine, id_client, fecha_asignacion)
                    VALUES (%s, %s, %s)
                    """,
                    (ROUTINE_ID, CLIENT_ID, START_DATE),
                )

        with self.assertRaises(psycopg.errors.UniqueViolation):
            asyncio.run(scenario())
        self.assertEqual(0, _assignment_count())


if __name__ == "__main__":
    unittest.main()
