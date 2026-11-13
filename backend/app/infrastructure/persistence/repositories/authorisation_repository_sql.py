"""PostgreSQL persistence for trainer-program authorizations."""

from __future__ import annotations

from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation

from app.application.exceptions import DuplicateResource, InvalidInput
from app.domain.entities.authorisation import Authorisation
from app.domain.repositories.authorisation_repository import AuthorisationRepository


class AuthorisationRepositorySql(AuthorisationRepository):
    def __init__(self, transaction_manager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        connection = self._tm.connection()
        if connection is None:
            raise RuntimeError("No transaction active for authorization persistence.")
        return connection

    @staticmethod
    def _entity(row: dict) -> Authorisation:
        return Authorisation(**row)

    async def create(self, authorisation: Authorisation) -> Authorisation:
        try:
            cursor = await self._conn.execute(
                """INSERT INTO authorises
                   (id_trainer, id_workout_program, can_generate, can_validate, start_date, end_date)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   RETURNING id_trainer, id_workout_program, can_generate, can_validate, start_date, end_date""",
                (authorisation.id_trainer, authorisation.id_workout_program,
                 authorisation.can_generate, authorisation.can_validate,
                 authorisation.start_date, authorisation.end_date),
            )
            return self._entity(await cursor.fetchone())
        except UniqueViolation as error:
            raise DuplicateResource("trainer-program authorization", "this trainer already has an authorization for this program") from error
        except (CheckViolation, ForeignKeyViolation) as error:
            raise InvalidInput(error.diag.message_primary) from error

    async def get(self, id_trainer: int, id_workout_program: int) -> Authorisation | None:
        cursor = await self._conn.execute(
            "SELECT id_trainer, id_workout_program, can_generate, can_validate, start_date, end_date FROM authorises WHERE id_trainer = %s AND id_workout_program = %s",
            (id_trainer, id_workout_program),
        )
        row = await cursor.fetchone()
        return self._entity(row) if row else None

    async def list(self, id_trainer: int | None = None, id_workout_program: int | None = None) -> list[Authorisation]:
        cursor = await self._conn.execute(
            """SELECT id_trainer, id_workout_program, can_generate, can_validate, start_date, end_date
               FROM authorises WHERE (%s::integer IS NULL OR id_trainer = %s)
               AND (%s::integer IS NULL OR id_workout_program = %s)
               ORDER BY id_trainer, id_workout_program""",
            (id_trainer, id_trainer, id_workout_program, id_workout_program),
        )
        return [self._entity(row) for row in await cursor.fetchall()]

    async def update(self, authorisation: Authorisation) -> Authorisation | None:
        try:
            cursor = await self._conn.execute(
                """UPDATE authorises SET can_generate = %s, can_validate = %s,
                   start_date = %s, end_date = %s WHERE id_trainer = %s AND id_workout_program = %s
                   RETURNING id_trainer, id_workout_program, can_generate, can_validate, start_date, end_date""",
                (authorisation.can_generate, authorisation.can_validate, authorisation.start_date,
                 authorisation.end_date, authorisation.id_trainer, authorisation.id_workout_program),
            )
            row = await cursor.fetchone()
            return self._entity(row) if row else None
        except (CheckViolation, ForeignKeyViolation) as error:
            raise InvalidInput(error.diag.message_primary) from error

    async def delete(self, id_trainer: int, id_workout_program: int) -> bool:
        cursor = await self._conn.execute(
            "DELETE FROM authorises WHERE id_trainer = %s AND id_workout_program = %s RETURNING id_trainer",
            (id_trainer, id_workout_program),
        )
        return await cursor.fetchone() is not None
