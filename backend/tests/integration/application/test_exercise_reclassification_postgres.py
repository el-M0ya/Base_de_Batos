"""PostgreSQL integration tests for exercise reclassification.

The suite applies only the schema scripts needed by the exercise bank and seeds
the catalog values used by the use case. It exercises the real SQL repositories
and the creator/role/conflict rules required by RF-15 and U-12.

The tests are skipped when the configured PostgreSQL instance is unreachable,
so the unit suite can run on machines without a database.
"""

from __future__ import annotations

import asyncio
import os
import unittest

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from backend.tests.integration.support import database

# Honour the same environment variables used by the rest of the integration
# suite, including alternate local ports.
database.TEST_DB_HOST = os.environ.get(
    "TEST_POSTGRES_HOST", database.TEST_DB_HOST
)
database.TEST_DB_PORT = int(
    os.environ.get("TEST_POSTGRES_PORT", str(database.TEST_DB_PORT))
)
database.TEST_DB_USER = os.environ.get(
    "TEST_POSTGRES_USER", database.TEST_DB_USER
)
database.TEST_DB_PASSWORD = os.environ.get(
    "TEST_POSTGRES_PASSWORD", database.TEST_DB_PASSWORD
)

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.application.dto.actor import ActorDTO
from app.application.dto.exercise_dto import ReclassifyExerciseInputDTO
from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.application.use_cases.reclassify_exercise import ReclassifyExerciseUseCase
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence import connection as db_connection
from app.infrastructure.persistence.repositories.catalog_repository_sql import (
    CatalogRepositorySql,
)
from app.infrastructure.persistence.repositories.exercise_repository_sql import (
    ExerciseRepositorySql,
)
from app.infrastructure.persistence.transaction import PsqlTransactionManager


TRAINER = ActorDTO(id_user=1, role=UserRole.TRAINER)
OTHER_TRAINER = ActorDTO(id_user=2, role=UserRole.TRAINER)
ADMIN = ActorDTO(id_user=3, role=UserRole.ADMIN)
CLIENT = ActorDTO(id_user=4, role=UserRole.CLIENT)

CHEST = MuscleGroup(id_muscle_group=1, name="Pectoral")
BACK = MuscleGroup(id_muscle_group=2, name="Espalda")

EXERCISE_SCRIPTS = database.SCRIPT_FILES[:4]
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


class ExerciseReclassificationIntegrationTests(unittest.IsolatedAsyncioTestCase):
    """Database-backed tests for the reclassification use case."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            asyncio.run(cls._prepare_database())
        except (psycopg.OperationalError, OSError) as error:
            raise unittest.SkipTest(
                f"PostgreSQL is not available for the integration suite: {error}"
            ) from error

    @classmethod
    async def _prepare_database(cls) -> None:
        await database.drop_test_database()
        await database.create_test_database()
        cls._apply_schema_subset()

    @staticmethod
    def _apply_schema_subset() -> None:
        connection = psycopg.connect(database._target_db_dsn(), autocommit=True)
        try:
            with connection.cursor() as cursor:
                for script_name in EXERCISE_SCRIPTS:
                    script = database.SCRIPTS_DIR / script_name
                    cursor.execute(script.read_text(encoding="utf-8"))
        finally:
            connection.close()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            asyncio.run(database.drop_test_database())
        except (psycopg.OperationalError, OSError):
            # The database may already be gone; cleanup must not hide the test
            # results in that case.
            pass

    async def asyncSetUp(self) -> None:
        self.pool = AsyncConnectionPool(
            conninfo=database._target_db_dsn(),
            min_size=1,
            max_size=5,
            timeout=30,
            open=False,
            kwargs={"row_factory": dict_row},
            name="e5-01-exercise-test-pool",
        )
        await self.pool.open(wait=True, timeout=30)

        async with self.pool.connection() as connection:
            await connection.execute(TRUNCATE_SQL)
            await connection.execute(
                """
                INSERT INTO app_user (id_user, name, email, password_hash, role)
                VALUES
                    (1, 'Trainer One', 'trainer-one@example.com', 'hash', 'TRAINER'),
                    (2, 'Trainer Two', 'trainer-two@example.com', 'hash', 'TRAINER')
                """
            )
            await connection.execute(
                """
                INSERT INTO trainer (id_trainer, specialty)
                VALUES (1, 'GENERAL'), (2, 'GENERAL')
                """
            )
            await connection.execute(
                """
                INSERT INTO muscle_group (id_muscle_group, name)
                VALUES (1, 'Pectoral'), (2, 'Espalda')
                """
            )
            await connection.execute(
                """
                INSERT INTO exercise_type (name)
                VALUES ('fuerza'), ('cardio'), ('flexibilidad')
                """
            )

        # The SQL repository and catalog adapter use the process-wide pool.
        db_connection._pool = self.pool

    async def asyncTearDown(self) -> None:
        db_connection._pool = None
        await self.pool.close()

    def _tm(self) -> PsqlTransactionManager:
        return PsqlTransactionManager()

    async def _create_exercise(
        self,
        *,
        name: str = "Press de banca",
        muscle_group: MuscleGroup = CHEST,
        creator: int = 1,
    ) -> Exercise:
        async with self._tm() as manager:
            repository = ExerciseRepositorySql(manager)
            return await repository.save(
                Exercise(
                    name=name,
                    description="Barra y banco",
                    exercise_type=ExerciseType.STRENGTH,
                    intensity=IntensityLevel.HIGH,
                    muscle_group=muscle_group,
                    id_trainer_creator=creator,
                )
            )

    async def _reclassify(
        self,
        id_exercise: int,
        *,
        actor: ActorDTO = TRAINER,
        exercise_type: str = "cardio",
        intensity: str = "low",
        muscle_group_id: int = BACK.id_muscle_group,
    ):
        async with self._tm() as manager:
            use_case = ReclassifyExerciseUseCase(
                ExerciseRepositorySql(manager),
                CatalogRepositorySql(manager),
            )
            return await use_case.execute(
                ReclassifyExerciseInputDTO(
                    actor=actor,
                    id_exercise=id_exercise,
                    exercise_type=exercise_type,
                    intensity=intensity,
                    muscle_group_id=muscle_group_id,
                )
            )

    async def _load(self, id_exercise: int) -> Exercise:
        async with self._tm() as manager:
            repository = ExerciseRepositorySql(manager)
            exercise = await repository.get_by_id(id_exercise)
            self.assertIsNotNone(exercise)
            return exercise

    async def test_creator_reclassifies_through_the_sql_repositories(self) -> None:
        exercise = await self._create_exercise()

        output = await self._reclassify(exercise.id_exercise)

        self.assertEqual(output.id_exercise, exercise.id_exercise)
        self.assertEqual(output.name, exercise.name)
        self.assertEqual(output.description, exercise.description)
        self.assertEqual(output.registration_date, exercise.registration_date)
        self.assertEqual(output.trainer_id, TRAINER.id_user)
        self.assertEqual(output.exercise_type, "cardio")
        self.assertEqual(output.intensity, "bajo")
        self.assertEqual(output.muscle_group_id, BACK.id_muscle_group)
        self.assertEqual(output.muscle_group_name, BACK.name)

        stored = await self._load(exercise.id_exercise)
        self.assertIs(stored.exercise_type, ExerciseType.CARDIO)
        self.assertIs(stored.intensity, IntensityLevel.LOW)
        self.assertEqual(stored.muscle_group, BACK)

    async def test_another_trainer_cannot_reclassify(self) -> None:
        exercise = await self._create_exercise()

        with self.assertRaises(PermissionDenied):
            await self._reclassify(exercise.id_exercise, actor=OTHER_TRAINER)

        stored = await self._load(exercise.id_exercise)
        self.assertIs(stored.exercise_type, ExerciseType.STRENGTH)
        self.assertEqual(stored.muscle_group, CHEST)

    async def test_administrator_and_client_cannot_reclassify(self) -> None:
        exercise = await self._create_exercise()

        for actor in (ADMIN, CLIENT):
            with self.subTest(role=actor.role.value):
                with self.assertRaises(PermissionDenied):
                    await self._reclassify(exercise.id_exercise, actor=actor)

        stored = await self._load(exercise.id_exercise)
        self.assertEqual(stored.muscle_group, CHEST)

    async def test_unknown_muscle_group_is_rejected(self) -> None:
        exercise = await self._create_exercise()

        with self.assertRaises(ResourceNotFound) as context:
            await self._reclassify(
                exercise.id_exercise,
                muscle_group_id=99,
            )

        self.assertEqual(context.exception.resource, "muscle group")
        stored = await self._load(exercise.id_exercise)
        self.assertEqual(stored.muscle_group, CHEST)

    async def test_invalid_catalog_values_are_rejected(self) -> None:
        exercise = await self._create_exercise()

        for exercise_type, intensity in (("yoga", "low"), ("cardio", "extremo")):
            with self.subTest(exercise_type=exercise_type, intensity=intensity):
                with self.assertRaises(InvalidInput):
                    await self._reclassify(
                        exercise.id_exercise,
                        exercise_type=exercise_type,
                        intensity=intensity,
                    )

        stored = await self._load(exercise.id_exercise)
        self.assertIs(stored.exercise_type, ExerciseType.STRENGTH)
        self.assertIs(stored.intensity, IntensityLevel.HIGH)

    async def test_u12_conflict_with_the_target_muscle_group_is_rejected(self) -> None:
        exercise = await self._create_exercise(name="Remo")
        duplicate = await self._create_exercise(name="  remo  ", muscle_group=BACK)

        with self.assertRaises(DuplicateResource) as context:
            await self._reclassify(exercise.id_exercise)

        error = context.exception
        self.assertEqual(error.resource, "exercise")
        self.assertEqual(error.existing.id_exercise, duplicate.id_exercise)

        stored = await self._load(exercise.id_exercise)
        self.assertEqual(stored.muscle_group, CHEST)
        self.assertIs(stored.exercise_type, ExerciseType.STRENGTH)

    async def test_reclassifying_to_the_current_classification_is_allowed(self) -> None:
        exercise = await self._create_exercise()

        output = await self._reclassify(
            exercise.id_exercise,
            exercise_type="strength",
            intensity="high",
            muscle_group_id=CHEST.id_muscle_group,
        )

        self.assertEqual(output.muscle_group_id, CHEST.id_muscle_group)
        self.assertEqual(output.exercise_type, "fuerza")
        self.assertEqual(output.intensity, "alto")

    async def test_missing_exercise_is_rejected(self) -> None:
        with self.assertRaises(ResourceNotFound) as context:
            await self._reclassify(999)

        self.assertEqual(context.exception.resource, "exercise")


if __name__ == "__main__":
    unittest.main()
