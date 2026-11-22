"""PostgreSQL implementation of the user repository."""

from __future__ import annotations

from typing import Optional

from psycopg.errors import CheckViolation, UniqueViolation

from app.application.exceptions import DuplicateResource, InvalidInput, ResourceNotFound
from app.domain.entities.client import Client
from app.domain.entities.trainer import Trainer, TrainerSpecialty
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.user_role import UserRole

_COLUMNS = (
    "id_user, name, email, password_hash, role, registration_date, is_active"
)


class UserRepositorySql(UserRepository):
    """Read and write user accounts using parameterized SQL.

    User and specialization writes (``app_user`` plus ``trainer`` or ``client``)
    run on the connection held by the request-scoped transaction manager, so
    multi-table operations are transactional.
    """

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

    async def list_users(self) -> tuple[User, ...]:
        """Return every user account, ordered by identifier."""
        cursor = await self._conn.execute(
            f"SELECT {_COLUMNS} FROM app_user ORDER BY id_user"
        )
        rows = await cursor.fetchall()
        return tuple(self._entity(row) for row in rows)

    async def get_profile(self, id_user: int) -> Trainer | Client | None:
        """Return the specialization profile associated with a user, or ``None``."""
        cursor = await self._conn.execute(
            "SELECT role FROM app_user WHERE id_user = %s",
            (id_user,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        role = UserRole.from_value(row["role"])
        user = User(id_user=id_user, role=role)

        if role is UserRole.TRAINER:
            cursor = await self._conn.execute(
                "SELECT id_trainer, specialty FROM trainer WHERE id_trainer = %s",
                (id_user,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return Trainer(
                user=user,
                specialty=TrainerSpecialty(row["specialty"]),
                id_trainer=row["id_trainer"],
            )

        if role is UserRole.CLIENT:
            cursor = await self._conn.execute(
                "SELECT id_client, age, id_site FROM client WHERE id_client = %s",
                (id_user,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return Client(
                user=user,
                age=row["age"],
                id_site=row["id_site"],
                id_client=row["id_client"],
            )

        return None

    async def save(
        self,
        user: User,
        profile: Trainer | Client | None = None,
    ) -> User:
        """Insert a new user and its optional specialization profile atomically."""
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
            raise InvalidInput("the user insert did not return an identifier")
        saved = self._entity(row)

        if profile is not None:
            if isinstance(profile, Trainer):
                await self._conn.execute(
                    "INSERT INTO trainer (id_trainer, specialty) VALUES (%s, %s)",
                    (saved.id_user, profile.specialty.value),
                )
            elif isinstance(profile, Client):
                await self._conn.execute(
                    "INSERT INTO client (id_client, age, id_site) VALUES (%s, %s, %s)",
                    (saved.id_user, profile.age, profile.id_site),
                )

        return saved

    async def update(
        self,
        user: User,
        profile: Trainer | Client | None = None,
    ) -> User:
        """Update an existing user and its specialization profile atomically."""
        try:
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
            raise ResourceNotFound("user", user.id_user)
        saved = self._entity(row)

        if profile is not None:
            if isinstance(profile, Trainer):
                await self._conn.execute(
                    "DELETE FROM trainer WHERE id_trainer = %s", (saved.id_user,)
                )
                await self._conn.execute(
                    "INSERT INTO trainer (id_trainer, specialty) VALUES (%s, %s)",
                    (saved.id_user, profile.specialty.value),
                )
            elif isinstance(profile, Client):
                await self._conn.execute(
                    "DELETE FROM client WHERE id_client = %s", (saved.id_user,)
                )
                await self._conn.execute(
                    "INSERT INTO client (id_client, age, id_site) VALUES (%s, %s, %s)",
                    (saved.id_user, profile.age, profile.id_site),
                )

        return saved

    async def deactivate(self, id_user: int) -> User:
        """Deactivate an account without deleting its historical records."""
        cursor = await self._conn.execute(
            f"UPDATE app_user SET is_active = FALSE WHERE id_user = %s RETURNING {_COLUMNS}",
            (id_user,),
        )
        row = await cursor.fetchone()
        if row is None:
            raise ResourceNotFound("user", id_user)
        return self._entity(row)
