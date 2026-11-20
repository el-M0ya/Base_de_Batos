"""Test-data builders for integration tests.

Builders insert rows directly into the database and return the corresponding
domain entities. They respect the role/specialization consistency trigger from
E1-08: a user is inserted into ``app_user`` first with the correct role, and
only then is the ``trainer`` or ``client`` row created with the same id.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import psycopg

from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.site import Site
from app.domain.entities.user import User
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.domain.value_objects.user_role import UserRole

from backend.tests.integration.support.database import _target_db_dsn

TEST_TRAINER_ID = 1001
TEST_CLIENT_ID = 1002
TEST_SITE_ID = 1
TEST_MUSCLE_GROUP_ID = 1


def _connect() -> psycopg.Connection:
    return psycopg.connect(_target_db_dsn(), autocommit=True)


def build_site(
    name: str = "Gimnasio Central",
    address: str = "Av. Siempre Viva 123",
    id_site: Optional[int] = None,
) -> Site:
    """Insert a site and return its domain entity."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            if id_site is not None:
                cur.execute(
                    "INSERT INTO site (id_site, name, address) VALUES (%s, %s, %s) RETURNING id_site, name, address, registration_date",
                    (id_site, name, address),
                )
            else:
                cur.execute(
                    "INSERT INTO site (name, address) VALUES (%s, %s) RETURNING id_site, name, address, registration_date",
                    (name, address),
                )
            row = cur.fetchone()
            return Site(
                id_site=row[0],
                name=row[1],
                address=row[2],
                created_at=row[3],
            )
    finally:
        conn.close()


def build_muscle_group(
    id_muscle_group: int = TEST_MUSCLE_GROUP_ID,
    name: str = "Pecho",
) -> MuscleGroup:
    """Insert a muscle group and return its domain entity."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO muscle_group (id_muscle_group, name) VALUES (%s, %s) RETURNING id_muscle_group, name",
                (id_muscle_group, name),
            )
            row = cur.fetchone()
            return MuscleGroup(id_muscle_group=row[0], name=row[1])
    finally:
        conn.close()


def build_user(
    name: str = "Entrenador Test",
    email: str = "entrenador.test@ejemplo.com",
    password_hash: str = "$2b$12$hash",
    role: UserRole = UserRole.TRAINER,
    id_user: Optional[int] = None,
) -> User:
    """Insert an app_user and return its domain entity."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            if id_user is not None:
                cur.execute(
                    "INSERT INTO app_user (id_user, name, email, password_hash, role) VALUES (%s, %s, %s, %s, %s) RETURNING id_user, name, email, password_hash, role, registration_date, active",
                    (id_user, name, email, password_hash, role.value),
                )
            else:
                cur.execute(
                    "INSERT INTO app_user (name, email, password_hash, role) VALUES (%s, %s, %s, %s) RETURNING id_user, name, email, password_hash, role, registration_date, active",
                    (name, email, password_hash, role.value),
                )
            row = cur.fetchone()
            return User(
                id_user=row[0],
                name=row[1],
                email=row[2],
                password_hash=row[3],
                role=UserRole.from_value(row[4]),
                created_at=row[5],
                active=row[6],
            )
    finally:
        conn.close()


def build_trainer(
    user: Optional[User] = None,
    specialty: str = "GENERAL",
    id_trainer: Optional[int] = None,
) -> User:
    """Insert a trainer profile for an existing TRAINER user and return the user.

    Respects the E1-08 trigger: the user must already exist in ``app_user`` with
    role ``TRAINER``.
    """
    if user is None:
        user = build_user(id_user=id_trainer or TEST_TRAINER_ID)
    elif user.role is not UserRole.TRAINER:
        raise ValueError("A trainer user must have role TRAINER.")

    trainer_id = id_trainer or user.id_user or TEST_TRAINER_ID
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO trainer (id_trainer, specialty) VALUES (%s, %s)",
                (trainer_id, specialty),
            )
    finally:
        conn.close()
    return user


def build_client(
    user: Optional[User] = None,
    age: int = 30,
    id_site: int = TEST_SITE_ID,
    id_client: Optional[int] = None,
) -> User:
    """Insert a client profile for an existing CLIENT user and return the user.

    Respects the E1-08 trigger: the user must already exist in ``app_user`` with
    role ``CLIENT``.
    """
    if user is None:
        user = build_user(
            id_user=id_client or TEST_CLIENT_ID,
            role=UserRole.CLIENT,
            email="cliente.test@ejemplo.com",
            name="Cliente Test",
        )
    elif user.role is not UserRole.CLIENT:
        raise ValueError("A client user must have role CLIENT.")

    client_id = id_client or user.id_user or TEST_CLIENT_ID
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO client (id_client, age, id_site) VALUES (%s, %s, %s)",
                (client_id, age, id_site),
            )
    finally:
        conn.close()
    return user


def build_workout_program(
    name: str = "Programa Fuerza",
    objective: str = "Hipertrofia",
    id_workout_program: Optional[int] = None,
) -> int:
    """Insert a workout program and return its identifier."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            if id_workout_program is not None:
                cur.execute(
                    "INSERT INTO workout_program (id_workout_program, name, objective) VALUES (%s, %s, %s) RETURNING id_workout_program",
                    (id_workout_program, name, objective),
                )
            else:
                cur.execute(
                    "INSERT INTO workout_program (name, objective) VALUES (%s, %s) RETURNING id_workout_program",
                    (name, objective),
                )
            row = cur.fetchone()
            return row[0]
    finally:
        conn.close()


def build_exercise(
    name: str = "Press de banca",
    exercise_type: str = "fuerza",
    intensity: str = "alto",
    muscle_group: Optional[MuscleGroup] = None,
    id_trainer_creator: int = TEST_TRAINER_ID,
    description: Optional[str] = None,
    registration_date: Optional[date] = None,
    id_exercise: Optional[int] = None,
) -> Exercise:
    """Insert an exercise and return its domain entity.

    Requires the referenced muscle group, exercise type and trainer to already
    exist in the database.
    """
    if muscle_group is None:
        muscle_group = build_muscle_group()

    conn = _connect()
    try:
        with conn.cursor() as cur:
            if id_exercise is not None:
                cur.execute(
                    """
                    INSERT INTO exercise (id_exercise, name, description, registration_date,
                        id_exercise_type, id_muscle_group, id_trainer_creator, intensity)
                    VALUES (%s, %s, %s, %s,
                        (SELECT id_exercise_type FROM exercise_type WHERE name = %s),
                        %s, %s, %s)
                    RETURNING id_exercise, name, description, registration_date,
                        id_exercise_type, id_muscle_group, id_trainer_creator, intensity
                    """,
                    (
                        id_exercise,
                        name,
                        description,
                        registration_date or date.today(),
                        exercise_type,
                        muscle_group.id_muscle_group,
                        id_trainer_creator,
                        intensity,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO exercise (name, description, registration_date,
                        id_exercise_type, id_muscle_group, id_trainer_creator, intensity)
                    VALUES (%s, %s, %s,
                        (SELECT id_exercise_type FROM exercise_type WHERE name = %s),
                        %s, %s, %s)
                    RETURNING id_exercise, name, description, registration_date,
                        id_exercise_type, id_muscle_group, id_trainer_creator, intensity
                    """,
                    (
                        name,
                        description,
                        registration_date or date.today(),
                        exercise_type,
                        muscle_group.id_muscle_group,
                        id_trainer_creator,
                        intensity,
                    ),
                )
            row = cur.fetchone()
            return Exercise(
                id_exercise=row[0],
                name=row[1],
                description=row[2],
                registration_date=row[3],
                exercise_type=ExerciseType.from_value(row[4]),
                muscle_group=MuscleGroup(
                    id_muscle_group=row[5], name=muscle_group.name
                ),
                id_trainer_creator=row[6],
                intensity=IntensityLevel.from_value(row[7]),
            )
    finally:
        conn.close()
