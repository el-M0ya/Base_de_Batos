"""PostgreSQL adapter for client enrollment persistence."""

from __future__ import annotations

from psycopg import AsyncConnection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.application.exceptions import DuplicateResource, ResourceNotFound
from app.domain.entities.enrolment import Enrolment
from app.domain.repositories.enrolment_repository import EnrolmentRepository


class EnrolmentRepositorySql(EnrolmentRepository):
    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def client_exists(self, id_client: int) -> bool:
        cursor = await self._connection.execute(
            "SELECT EXISTS (SELECT 1 FROM client WHERE id_client = %s) AS present",
            (id_client,),
        )
        row = await cursor.fetchone()
        return bool(row["present"])

    async def workout_program_exists(self, id_workout_program: int) -> bool:
        cursor = await self._connection.execute(
            "SELECT EXISTS (SELECT 1 FROM workout_program WHERE id_workout_program = %s) AS present",
            (id_workout_program,),
        )
        row = await cursor.fetchone()
        return bool(row["present"])

    async def get(self, id_client: int, id_workout_program: int) -> Enrolment | None:
        cursor = await self._connection.execute(
            """SELECT id_client, id_workout_program, enrollment_date
               FROM inscribed WHERE id_client = %s AND id_workout_program = %s""",
            (id_client, id_workout_program),
        )
        row = await cursor.fetchone()
        return Enrolment(**row) if row else None

    async def create(self, enrolment: Enrolment) -> Enrolment:
        try:
            cursor = await self._connection.execute(
                """INSERT INTO inscribed (id_client, id_workout_program, enrollment_date)
                   VALUES (%s, %s, %s)
                   RETURNING id_client, id_workout_program, enrollment_date""",
                (enrolment.id_client, enrolment.id_workout_program,
                 enrolment.enrollment_date),
            )
            row = await cursor.fetchone()
            if row is None:
                raise RuntimeError("The enrollment insert returned no row.")
            return Enrolment(**row)
        except UniqueViolation as error:
            raise DuplicateResource(
                "enrollment",
                "the client is already enrolled in this workout program",
            ) from error
        except ForeignKeyViolation as error:
            constraint = error.diag.constraint_name
            if constraint == "fk_inscribed_client":
                raise ResourceNotFound("client", enrolment.id_client) from error
            if constraint == "fk_inscribed_workout_program":
                raise ResourceNotFound(
                    "workout program", enrolment.id_workout_program
                ) from error
            raise

    async def list_for_client(self, id_client: int) -> list[Enrolment]:
        cursor = await self._connection.execute(
            """SELECT id_client, id_workout_program, enrollment_date
               FROM inscribed WHERE id_client = %s
               ORDER BY enrollment_date DESC, id_workout_program""",
            (id_client,),
        )
        return [Enrolment(**row) for row in await cursor.fetchall()]
