"""Builders of valid test data for the integration tests.

Every builder inserts directly through the given cursor, inside the transaction
opened by the test. ``create_trainer`` and ``create_client`` insert the
``app_user`` row and its specialization in the same transaction and in the order
accepted by the E1-08 triggers (``trg_check_trainer_user_role`` /
``trg_check_client_user_role``): the user first, then the specialization.
"""

from __future__ import annotations

import uuid
from typing import Optional

from psycopg import AsyncCursor

PASSWORD_HASH = "not-a-real-hash"


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


async def create_site(
    cursor: AsyncCursor,
    name: Optional[str] = None,
    address: str = "Calle 1, Vedado",
) -> int:
    await cursor.execute(
        "INSERT INTO site (name, address) VALUES (%s, %s) RETURNING id_site",
        (name or _unique("Sede"), address),
    )
    return (await cursor.fetchone())["id_site"]


async def create_muscle_group(cursor: AsyncCursor, name: Optional[str] = None) -> int:
    await cursor.execute(
        "INSERT INTO muscle_group (name) VALUES (%s) RETURNING id_muscle_group",
        (name or _unique("Grupo"),),
    )
    return (await cursor.fetchone())["id_muscle_group"]


async def create_exercise_type(cursor: AsyncCursor, name: str = "fuerza") -> int:
    await cursor.execute(
        """
        INSERT INTO exercise_type (name) VALUES (%s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id_exercise_type
        """,
        (name,),
    )
    row = await cursor.fetchone()
    if row is not None:
        return row["id_exercise_type"]
    await cursor.execute(
        "SELECT id_exercise_type FROM exercise_type WHERE name = %s", (name,)
    )
    return (await cursor.fetchone())["id_exercise_type"]


async def create_intensity_level(cursor: AsyncCursor, name: str = "alto") -> int:
    await cursor.execute(
        """
        INSERT INTO intensity_level (name) VALUES (%s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id_intensity_level
        """,
        (name,),
    )
    row = await cursor.fetchone()
    if row is not None:
        return row["id_intensity_level"]
    await cursor.execute(
        "SELECT id_intensity_level FROM intensity_level WHERE name = %s", (name,)
    )
    return (await cursor.fetchone())["id_intensity_level"]


async def create_user(
    cursor: AsyncCursor,
    role: str = "TRAINER",
    name: Optional[str] = None,
    email: Optional[str] = None,
) -> int:
    await cursor.execute(
        """
        INSERT INTO app_user (name, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
        RETURNING id_user
        """,
        (
            name or _unique("Usuario"),
            email or f"{uuid.uuid4().hex[:10]}@example.com",
            PASSWORD_HASH,
            role,
        ),
    )
    return (await cursor.fetchone())["id_user"]


async def create_trainer(
    cursor: AsyncCursor,
    specialty: str = "GENERAL",
    email: Optional[str] = None,
) -> int:
    """Insert the user and its trainer specialization inside the same transaction."""
    user_id = await create_user(cursor, role="TRAINER", email=email)
    await cursor.execute(
        "INSERT INTO trainer (id_trainer, specialty) VALUES (%s, %s)",
        (user_id, specialty),
    )
    return user_id


async def create_client(
    cursor: AsyncCursor,
    site_id: Optional[int] = None,
    age: int = 30,
    email: Optional[str] = None,
) -> int:
    """Insert the user and its client specialization inside the same transaction."""
    if site_id is None:
        site_id = await create_site(cursor)
    user_id = await create_user(cursor, role="CLIENT", email=email)
    await cursor.execute(
        "INSERT INTO client (id_client, age, id_site) VALUES (%s, %s, %s)",
        (user_id, age, site_id),
    )
    return user_id


async def create_workout_program(
    cursor: AsyncCursor,
    name: Optional[str] = None,
    objective: str = "Mejorar la fuerza general",
) -> int:
    await cursor.execute(
        """
        INSERT INTO workout_program (name, objective)
        VALUES (%s, %s)
        RETURNING id_workout_program
        """,
        (name or _unique("Programa"), objective),
    )
    return (await cursor.fetchone())["id_workout_program"]


async def create_exercise(
    cursor: AsyncCursor,
    id_trainer: int,
    id_muscle_group: int,
    name: Optional[str] = None,
    exercise_type: str = "fuerza",
    intensity: str = "alto",
    description: Optional[str] = "Ejercicio de prueba",
) -> int:
    type_id = await create_exercise_type(cursor, exercise_type)
    intensity_id = await create_intensity_level(cursor, intensity)
    await cursor.execute(
        """
        INSERT INTO exercise (
            name, description, id_exercise_type, id_intensity_level,
            id_muscle_group, id_trainer_creator
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id_exercise
        """,
        (
            name or _unique("Ejercicio"),
            description,
            type_id,
            intensity_id,
            id_muscle_group,
            id_trainer,
        ),
    )
    return (await cursor.fetchone())["id_exercise"]
