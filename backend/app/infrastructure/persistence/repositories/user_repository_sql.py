"""PostgreSQL implementation of the user repository."""

from __future__ import annotations

from typing import Optional

from psycopg.errors import CheckViolation, UniqueViolation

from app.application.exceptions import DuplicateResource, InvalidInput
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.user_role import UserRole

_COLUMNS = (
    "id_user, name, email, password_hash, role, registration_date, is_active"
)


class UserRepositorySql(UserRepository):
    """Read and write user accounts using parameterized SQL."""

    def __init__(self, transaction_manager) -> None:
        self._tm = transaction_manager

    @property
    def _conn(self):
        connection = self._tm.connection()
        if connection is None:
            raise RuntimeError("No transaction active for user persistence.")
        return connection

    @staticmethod
    def _entity(row: dict) -> User:
        return User(
            id_user=row["id_user"],
            name=row["name"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=UserRole.from_value(row["role"]),
            created_at=row["registration_date"],
            active=row["is_active"],
        )

    async def get_by_id(self, id_user: int) -> Optional[User]:
        cursor = await self._conn.execute(
            f"SELECT {_COLUMNS} FROM app_user WHERE id_user = %s",
            (id_user,),
        )
        row = await cursor.fetchone()
        return self._entity(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        cursor = await self._conn.execute(
            f"SELECT {_COLUMNS} FROM app_user WHERE LOWER(email) = LOWER(%s)",
            (email,),
        )
        row = await cursor.fetchone()
        return self._entity(row) if row else None

    async def save(self, user: User) -> User:
        try:
            if user.id_user is None:
                cursor = await self._conn.execute(
                    f"""INSERT INTO app_user (name, email, password_hash, role, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING {_COLUMNS}""",
                    (
                        user.name,
                        user.email,
                        user.password_hash,
                        user.role.value,
                        user.active,
                    ),
                )
            else:
                cursor = await self._conn.execute(
                    f"""UPDATE app_user
                        SET name = %s, email = %s, password_hash = %s,
                            role = %s, is_active = %s
                        WHERE id_user = %s
                        RETURNING {_COLUMNS}""",
                    (
                        user.name,
                        user.email,
                        user.password_hash,
                        user.role.value,
                        user.active,
                        user.id_user,
                    ),
                )
            row = await cursor.fetchone()
        except UniqueViolation as error:
            raise DuplicateResource(
                "user",
                "an account with that email already exists",
            ) from error
        except CheckViolation as error:
            raise InvalidInput(error.diag.message_primary) from error

        if row is None:
            raise InvalidInput("the user does not exist")
        return self._entity(row)
