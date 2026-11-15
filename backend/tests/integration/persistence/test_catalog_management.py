"""Integration tests for training program and muscle-group persistence.

The suite uses the shared test-database helpers but applies only the schema
scripts required by this issue (identity, catalogs/programs, authorisations,
enrolments and routines). This keeps the tests independent from unrelated
schema modules while still exercising real PostgreSQL constraints.
"""

from __future__ import annotations

import asyncio
import os
import unittest
from datetime import date

import psycopg
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from backend.tests.integration.support import database

# Allow the suite to run against a PostgreSQL instance on another port.
database.TEST_DB_PORT = int(
    os.environ.get("TEST_POSTGRES_PORT", str(database.TEST_DB_PORT))
)

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.application.dto.actor import ActorDTO
from app.application.dto.muscle_group_dto import CreateMuscleGroupInputDTO
from app.application.dto.training_program_dto import (
    CreateTrainingProgramInputDTO,
    DeleteTrainingProgramInputDTO,
    SetTrainingProgramMuscleGroupsInputDTO,
    UpdateTrainingProgramInputDTO,
)
from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    ResourceNotFound,
)
from app.application.services.muscle_group_resolver import MuscleGroupResolver
from app.application.use_cases.create_muscle_group import CreateMuscleGroupUseCase
from app.application.use_cases.create_training_program import (
    CreateTrainingProgramUseCase,
)
from app.application.use_cases.delete_training_program import (
    DeleteTrainingProgramUseCase,
)
from app.application.use_cases.set_training_program_muscle_groups import (
    SetTrainingProgramMuscleGroupsUseCase,
)
from app.application.use_cases.update_training_program import (
    UpdateTrainingProgramUseCase,
)
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.workout_program import WorkoutProgram
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence import connection as db_connection
from app.infrastructure.persistence.repositories.muscle_group_repository_sql import (
    MuscleGroupRepositorySql,
)
from app.infrastructure.persistence.repositories.workout_program_repository_sql import (
    WorkoutProgramRepositorySql,
)
from app.infrastructure.persistence.transaction import PsqlTransactionManager

ADMIN = ActorDTO(id_user=1, role=UserRole.ADMIN)
CATALOG_SCRIPTS = database.SCRIPT_FILES[:4]
TRUNCATE_SQL = """
TRUNCATE TABLE
    covers,
    workout_program,
    muscle_group,
    exercise_type,
    contains,
    routine_structure,
    routine,
    parameters_routine,
    inscribed,
    authorises,
    exercise,
    client,
    trainer,
    app_user,
    site
RESTART IDENTITY CASCADE
"""


class CatalogManagementIntegrationTests(unittest.IsolatedAsyncioTestCase):
    """Database-backed tests for catalog and program persistence."""

    @classmethod
    def setUpClass(cls) -> None:
        asyncio.run(cls._prepare_database())

    @classmethod
    async def _prepare_database(cls) -> None:
        await database.drop_test_database()
        await database.create_test_database()
        cls._apply_schema_subset()

    @staticmethod
    def _apply_schema_subset() -> None:
        connection = psycopg.connect(
            database._target_db_dsn(), autocommit=True
        )
        try:
            with connection.cursor() as cursor:
                for script_name in CATALOG_SCRIPTS:
                    script = database.SCRIPTS_DIR / script_name
                    cursor.execute(script.read_text(encoding="utf-8"))
        finally:
            connection.close()

    @classmethod
    def tearDownClass(cls) -> None:
        asyncio.run(database.drop_test_database())

    async def asyncSetUp(self) -> None:
        self.pool = AsyncConnectionPool(
            conninfo=database._target_db_dsn(),
            min_size=1,
            max_size=5,
            timeout=30,
            open=False,
            kwargs={"row_factory": dict_row},
            name="e4-04-catalog-test-pool",
        )
        await self.pool.open(wait=True, timeout=30)
        async with self.pool.connection() as connection:
            await connection.execute(TRUNCATE_SQL)
        db_connection._pool = self.pool

    async def asyncTearDown(self) -> None:
        db_connection._pool = None
        await self.pool.close()

    def _tm(self) -> PsqlTransactionManager:
        return PsqlTransactionManager()

    async def _create_referenced_program(
        self, manager: PsqlTransactionManager
    ) -> tuple[int, int, int, int, int]:
        """Create a trainer, client, enrolment, authorisation and program."""
        connection = manager.connection()
        assert connection is not None

        trainer_user = await self._scalar(
            connection,
            """
            INSERT INTO app_user (name, email, password_hash, role)
            VALUES ('Trainer', 'trainer@example.com', 'hash', 'TRAINER')
            RETURNING id_user
            """,
        )
        client_user = await self._scalar(
            connection,
            """
            INSERT INTO app_user (name, email, password_hash, role)
            VALUES ('Client', 'client@example.com', 'hash', 'CLIENT')
            RETURNING id_user
            """,
        )
        site_id = await self._scalar(
            connection,
            """
            INSERT INTO site (name, address)
            VALUES ('Main site', 'Main street')
            RETURNING id_site
            """,
        )
        await connection.execute(
            """
            INSERT INTO trainer (id_trainer, specialty)
            VALUES (%s, 'GENERAL')
            """,
            (trainer_user,),
        )
        await connection.execute(
            """
            INSERT INTO client (id_client, age, id_site)
            VALUES (%s, 25, %s)
            """,
            (client_user, site_id),
        )

        muscle_group = await MuscleGroupRepositorySql(manager).save(
            MuscleGroup(None, "Chest")
        )
        program = await WorkoutProgramRepositorySql(manager).save(
            WorkoutProgram(
                "Force",
                "Build strength",
                target_muscle_groups=[muscle_group],
            )
        )
        assert program.id_workout_program is not None
        assert muscle_group.id_muscle_group is not None

        await connection.execute(
            """
            INSERT INTO inscribed (id_client, id_workout_program, enrollment_date)
            VALUES (%s, %s, %s)
            """,
            (client_user, program.id_workout_program, date.today()),
        )
        await connection.execute(
            """
            INSERT INTO authorises (
                id_trainer, id_workout_program, can_generate, can_validate
            )
            VALUES (%s, %s, TRUE, FALSE)
            """,
            (trainer_user, program.id_workout_program),
        )
        return (
            trainer_user,
            client_user,
            program.id_workout_program,
            muscle_group.id_muscle_group,
            site_id,
        )

    @staticmethod
    async def _scalar(connection: AsyncConnection, sql: str):
        cursor = await connection.execute(sql)
        row = await cursor.fetchone()
        assert row is not None
        return next(iter(row.values()))

    async def test_muscle_group_crud_and_duplicate_name(self) -> None:
        async with self._tm() as manager:
            repository = MuscleGroupRepositorySql(manager)
            saved = await repository.save(MuscleGroup(None, "  Chest "))
            self.assertEqual(saved.name, "Chest")
            self.assertIsNotNone(saved.id_muscle_group)

            self.assertEqual((await repository.list())[0].name, "Chest")
            renamed = await repository.save(
                MuscleGroup(saved.id_muscle_group, "Pectoral")
            )
            self.assertEqual(renamed.name, "Pectoral")

            await repository.delete(saved.id_muscle_group)
            self.assertIsNone(await repository.get_by_id(saved.id_muscle_group))

        with self.assertRaises(DuplicateResource):
            async with self._tm() as manager:
                repository = MuscleGroupRepositorySql(manager)
                await repository.save(MuscleGroup(None, "Chest"))
                await repository.save(MuscleGroup(None, "Chest"))

    async def test_muscle_group_delete_is_blocked_when_referenced(self) -> None:
        with self.assertRaises(BusinessRuleViolation):
            async with self._tm() as manager:
                group_repository = MuscleGroupRepositorySql(manager)
                program_repository = WorkoutProgramRepositorySql(manager)
                group = await group_repository.save(MuscleGroup(None, "Chest"))
                await program_repository.save(
                    WorkoutProgram(
                        "Force",
                        "Build strength",
                        target_muscle_groups=[group],
                    )
                )
                await group_repository.delete(group.id_muscle_group)

    async def test_program_crud_associations_and_coverage_query(self) -> None:
        async with self._tm() as manager:
            group_repository = MuscleGroupRepositorySql(manager)
            program_repository = WorkoutProgramRepositorySql(manager)
            chest = await group_repository.save(MuscleGroup(None, "Chest"))
            back = await group_repository.save(MuscleGroup(None, "Back"))

            program = await program_repository.save(
                WorkoutProgram(
                    "Upper body",
                    "Build strength",
                    target_muscle_groups=[chest, back],
                )
            )
            self.assertIsNotNone(program.id_workout_program)
            loaded = await program_repository.get_by_id(
                program.id_workout_program
            )
            self.assertEqual(
                {group.name for group in loaded.target_muscle_groups},
                {"Chest", "Back"},
            )
            coverage = await program_repository.list_covered_muscle_groups(
                program.id_workout_program
            )
            self.assertEqual([group.name for group in coverage], ["Back", "Chest"])

            loaded.target_muscle_groups = [back]
            updated = await program_repository.save(loaded)
            self.assertEqual(
                [group.name for group in updated.target_muscle_groups],
                ["Back"],
            )
            self.assertEqual(
                [group.name for group in await program_repository.list()],
                ["Upper body"],
            )

            await program_repository.delete(program.id_workout_program)
            self.assertEqual(await program_repository.list(), [])

        with self.assertRaises(DuplicateResource):
            async with self._tm() as manager:
                repository = WorkoutProgramRepositorySql(manager)
                await repository.save(WorkoutProgram("Force", "Build strength"))
                await repository.save(WorkoutProgram("Force", "Build strength"))

    async def test_invalid_coverage_replacement_rolls_back_associations(
        self,
    ) -> None:
        async with self._tm() as manager:
            group_repository = MuscleGroupRepositorySql(manager)
            program_repository = WorkoutProgramRepositorySql(manager)
            chest = await group_repository.save(MuscleGroup(None, "Chest"))
            program = await program_repository.save(
                WorkoutProgram(
                    "Upper body",
                    "Build strength",
                    target_muscle_groups=[chest],
                )
            )
            program_id = program.id_workout_program

        with self.assertRaises(ResourceNotFound):
            async with self._tm() as manager:
                resolver = MuscleGroupResolver(MuscleGroupRepositorySql(manager))
                use_case = SetTrainingProgramMuscleGroupsUseCase(
                    WorkoutProgramRepositorySql(manager), resolver
                )
                await use_case.execute(
                    SetTrainingProgramMuscleGroupsInputDTO(
                        actor=ADMIN,
                        id_workout_program=program_id,
                        muscle_group_ids=(chest.id_muscle_group, 999999),
                    )
                )

        async with self._tm() as manager:
            program_repository = WorkoutProgramRepositorySql(manager)
            persisted = await program_repository.get_by_id(program_id)
            self.assertEqual(
                [group.name for group in persisted.target_muscle_groups],
                ["Chest"],
            )

    async def test_program_delete_is_blocked_by_authorisation_and_enrolment(
        self,
    ) -> None:
        with self.assertRaises(BusinessRuleViolation):
            async with self._tm() as manager:
                (
                    trainer_user,
                    client_user,
                    program_id,
                    _group_id,
                    _site_id,
                ) = await self._create_referenced_program(manager)
                program_repository = WorkoutProgramRepositorySql(manager)
                self.assertTrue(
                    await program_repository.is_client_enrolled(
                        client_user, program_id, date.today()
                    )
                )
                self.assertIsNotNone(
                    await program_repository.get_authorisation(
                        trainer_user, program_id
                    )
                )
                await program_repository.delete(program_id)

    async def test_use_cases_manage_programs_and_coverage(self) -> None:
        async with self._tm() as manager:
            group_repository = MuscleGroupRepositorySql(manager)
            program_repository = WorkoutProgramRepositorySql(manager)
            resolver = MuscleGroupResolver(group_repository)
            create_group = CreateMuscleGroupUseCase(group_repository)
            chest = await create_group.execute(
                CreateMuscleGroupInputDTO(actor=ADMIN, name="Chest")
            )
            back = await create_group.execute(
                CreateMuscleGroupInputDTO(actor=ADMIN, name="Back")
            )

            create_program = CreateTrainingProgramUseCase(
                program_repository, resolver
            )
            program = await create_program.execute(
                CreateTrainingProgramInputDTO(
                    actor=ADMIN,
                    name="Upper body",
                    objective="Build strength",
                    muscle_group_ids=(chest.id_muscle_group, back.id_muscle_group),
                )
            )
            self.assertEqual(
                set(program.muscle_group_ids),
                {chest.id_muscle_group, back.id_muscle_group},
            )

            set_coverage = SetTrainingProgramMuscleGroupsUseCase(
                program_repository, resolver
            )
            updated = await set_coverage.execute(
                SetTrainingProgramMuscleGroupsInputDTO(
                    actor=ADMIN,
                    id_workout_program=program.id_workout_program,
                    muscle_group_ids=(back.id_muscle_group,),
                )
            )
            self.assertEqual(updated.muscle_group_ids, (back.id_muscle_group,))

            update_program = UpdateTrainingProgramUseCase(
                program_repository, resolver
            )
            renamed = await update_program.execute(
                UpdateTrainingProgramInputDTO(
                    actor=ADMIN,
                    id_workout_program=program.id_workout_program,
                    name="Upper body advanced",
                    objective="Build maximal strength",
                    muscle_group_ids=(chest.id_muscle_group,),
                )
            )
            self.assertEqual(renamed.name, "Upper body advanced")
            self.assertEqual(renamed.muscle_group_ids, (chest.id_muscle_group,))

            delete_program = DeleteTrainingProgramUseCase(program_repository)
            await delete_program.execute(
                DeleteTrainingProgramInputDTO(
                    actor=ADMIN,
                    id_workout_program=program.id_workout_program,
                )
            )
            self.assertEqual(await program_repository.list(), [])

        with self.assertRaises(DuplicateResource):
            async with self._tm() as manager:
                group_repository = MuscleGroupRepositorySql(manager)
                program_repository = WorkoutProgramRepositorySql(manager)
                resolver = MuscleGroupResolver(group_repository)
                create_group = CreateMuscleGroupUseCase(group_repository)
                await create_group.execute(
                    CreateMuscleGroupInputDTO(actor=ADMIN, name="Chest")
                )
                create_program = CreateTrainingProgramUseCase(
                    program_repository, resolver
                )
                await create_program.execute(
                    CreateTrainingProgramInputDTO(
                        actor=ADMIN,
                        name="Upper body",
                        objective="Build strength",
                    )
                )
                await create_program.execute(
                    CreateTrainingProgramInputDTO(
                        actor=ADMIN,
                        name="upper BODY",
                        objective="Build strength",
                    )
                )


if __name__ == "__main__":
    unittest.main()
