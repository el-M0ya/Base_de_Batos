"""PostgreSQL implementation of the user repository contract."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, time
from typing import Any

from psycopg import AsyncConnection, errors

from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.domain.entities.client import Client
from app.domain.entities.trainer import Trainer
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.persistence.connection import (
    connection_scope,
    transaction_scope,
)


class PostgresUserRepository(UserRepository):
    """Persist users and their one-to-one specialization profiles."""

    async def get_by_id(self, id_user: int) -> User | None:
        async with connection_scope() as connection:
            cursor = await connection.execute(
                """
                SELECT id_user, name, email, password_hash, role, active,
                       registration_date
                FROM app_user
                WHERE id_user = %s
                """,
                (id_user,),
            )
            row = await cursor.fetchone()
        return _user_from_row(_as_mapping(row)) if row is not None else None

    async def get_by_email(self, email: str) -> User | None:
        async with connection_scope() as connection:
            cursor = await connection.execute(
                """
                SELECT id_user, name, email, password_hash, role, active,
                       registration_date
                FROM app_user
                WHERE email = %s
                """,
                (email,),
            )
            row = await cursor.fetchone()
        return _user_from_row(_as_mapping(row)) if row is not None else None

    async def list_users(self) -> tuple[User, ...]:
        async with connection_scope() as connection:
            cursor = await connection.execute(
                """
                SELECT id_user, name, email, password_hash, role, active,
                       registration_date
                FROM app_user
                ORDER BY id_user
                """
            )
            rows = await cursor.fetchall()
        return tuple(_user_from_row(_as_mapping(row)) for row in rows)

    async def get_profile(self, id_user: int) -> Trainer | Client | None:
        async with connection_scope() as connection:
            cursor = await connection.execute(
                """
                SELECT u.id_user, u.name, u.email, u.password_hash, u.role,
                       u.active, u.registration_date,
                       t.specialty AS trainer_specialty,
                       c.age AS client_age, c.id_site AS client_site
                FROM app_user AS u
                LEFT JOIN trainer AS t ON t.id_trainer = u.id_user
                LEFT JOIN client AS c ON c.id_client = u.id_user
                WHERE u.id_user = %s
                """,
                (id_user,),
            )
            raw_row = await cursor.fetchone()
        if raw_row is None:
            return None

        row = _as_mapping(raw_row)
        user = _user_from_row(row)
        if user.is_trainer() and row["trainer_specialty"] is not None:
            return Trainer(user=user, specialty=row["trainer_specialty"])
        if user.is_client() and row["client_age"] is not None:
            return Client(
                user=user,
                age=row["client_age"],
                id_site=row["client_site"],
            )
        return None

    async def save(
        self,
        user: User,
        profile: Trainer | Client | None = None,
    ) -> User:
        async with transaction_scope() as connection:
            try:
                cursor = await connection.execute(
                    """
                    INSERT INTO app_user (
                        name, email, password_hash, role, active
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id_user, registration_date
                    """,
                    (
                        user.name,
                        user.email,
                        user.password_hash,
                        user.role.value,
                        user.active,
                    ),
                )
                row = _as_mapping(await cursor.fetchone())
                user.id_user = row["id_user"]
                user.created_at = _as_datetime(row["registration_date"])
                await self._save_profile(connection, user, profile)
            except (
                errors.UniqueViolation,
                errors.ForeignKeyViolation,
                errors.CheckViolation,
                errors.RaiseException,
            ) as error:
                raise _translate_database_error(error, user, profile) from error
        return user

    async def update(
        self,
        user: User,
        profile: Trainer | Client | None = None,
    ) -> User:
        if user.id_user is None:
            raise InvalidInput("a persisted user identifier is required for update.")

        async with transaction_scope() as connection:
            try:
                cursor = await connection.execute(
                    """
                    UPDATE app_user
                    SET name = %s,
                        email = %s,
                        password_hash = %s,
                        role = %s,
                        active = %s
                    WHERE id_user = %s
                    RETURNING registration_date
                    """,
                    (
                        user.name,
                        user.email,
                        user.password_hash,
                        user.role.value,
                        user.active,
                        user.id_user,
                    ),
                )
                raw_row = await cursor.fetchone()
                if raw_row is None:
                    raise ResourceNotFound("user", user.id_user)
                row = _as_mapping(raw_row)
                user.created_at = _as_datetime(row["registration_date"])
                await self._update_profile(connection, user, profile)
            except (
                errors.UniqueViolation,
                errors.ForeignKeyViolation,
                errors.CheckViolation,
                errors.RaiseException,
            ) as error:
                raise _translate_database_error(error, user, profile) from error
        return user

    async def deactivate(self, id_user: int) -> User:
        async with transaction_scope() as connection:
            cursor = await connection.execute(
                """
                UPDATE app_user
                SET active = FALSE
                WHERE id_user = %s
                RETURNING id_user, name, email, password_hash, role, active,
                          registration_date
                """,
                (id_user,),
            )
            row = await cursor.fetchone()
            if row is None:
                raise ResourceNotFound("user", id_user)
        return _user_from_row(_as_mapping(row))

    async def _save_profile(
        self,
        connection: AsyncConnection[Any],
        user: User,
        profile: Trainer | Client | None,
    ) -> None:
        if profile is None:
            return
        if user.id_user is None:
            raise RuntimeError("The user identifier is required before saving a profile.")
        if isinstance(profile, Trainer):
            profile.id_trainer = user.id_user
            await connection.execute(
                """
                INSERT INTO trainer (id_trainer, specialty)
                VALUES (%s, %s)
                """,
                (profile.id_trainer, profile.specialty.value),
            )
        else:
            profile.id_client = user.id_user
            await connection.execute(
                """
                INSERT INTO client (id_client, age, id_site)
                VALUES (%s, %s, %s)
                """,
                (profile.id_client, profile.age, profile.id_site),
            )

    async def _update_profile(
        self,
        connection: AsyncConnection[Any],
        user: User,
        profile: Trainer | Client | None,
    ) -> None:
        if profile is None or user.id_user is None:
            return
        if isinstance(profile, Trainer):
            profile.id_trainer = user.id_user
            await connection.execute(
                """
                INSERT INTO trainer (id_trainer, specialty)
                VALUES (%s, %s)
                ON CONFLICT (id_trainer)
                DO UPDATE SET specialty = EXCLUDED.specialty
                """,
                (profile.id_trainer, profile.specialty.value),
            )
        else:
            profile.id_client = user.id_user
            await connection.execute(
                """
                INSERT INTO client (id_client, age, id_site)
                VALUES (%s, %s, %s)
                ON CONFLICT (id_client)
                DO UPDATE SET age = EXCLUDED.age, id_site = EXCLUDED.id_site
                """,
                (profile.id_client, profile.age, profile.id_site),
            )


def _as_mapping(row: object) -> Mapping[str, Any]:
    if not isinstance(row, Mapping):
        raise RuntimeError("The database row factory did not return a mapping.")
    return row


def _user_from_row(row: Mapping[str, Any]) -> User:
    return User(
        id_user=row["id_user"],
        name=row["name"],
        email=row["email"],
        password_hash=row["password_hash"],
        role=row["role"],
        active=row["active"],
        created_at=_as_datetime(row["registration_date"]),
    )


def _translate_database_error(
    error: errors.DatabaseError,
    user: User,
    profile: Trainer | Client | None,
) -> Exception:
    constraint_name = getattr(error.diag, "constraint_name", None)

    if isinstance(error, errors.UniqueViolation):
        if constraint_name in {"uq_app_user_email", "uq_user_email"}:
            return DuplicateResource(
                "user",
                f"email {user.email!r} is already registered.",
            )
        return DuplicateResource("user profile", "the profile already exists.")

    if isinstance(error, errors.ForeignKeyViolation):
        if constraint_name == "fk_client_site" and isinstance(profile, Client):
            return ResourceNotFound("site", profile.id_site)
        return ResourceNotFound("user", user.id_user or "unknown")

    if isinstance(error, errors.CheckViolation):
        if constraint_name == "chk_client_age" and isinstance(profile, Client):
            return InvalidInput(f"client age {profile.age!r} is outside the valid range.")
        return InvalidInput("user or profile data violates a database rule.")

    return InvalidInput("user or profile data violates a consistency rule.")


def _as_datetime(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min)
