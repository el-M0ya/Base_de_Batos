"""Integration tests for exercise registration through the HTTP API."""

from __future__ import annotations

import uuid

import psycopg
import pytest
from psycopg.rows import dict_row

try:
    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.main import app
except (ModuleNotFoundError, RuntimeError) as error:
    pytest.skip(f"API prerequisites are unavailable: {error}", allow_module_level=True)


pytestmark = pytest.mark.integration


def _connection():
    return psycopg.connect(get_settings().database_url, row_factory=dict_row)


def _database_ready() -> bool:
    try:
        with _connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT to_regclass('public.app_user'), "
                "to_regclass('public.exercise'), "
                "to_regclass('public.muscle_group')"
            )
            return all(cursor.fetchone())
    except (psycopg.Error, OSError):
        return False


@pytest.fixture(scope="module", autouse=True)
def require_database() -> None:
    if not _database_ready():
        pytest.skip("PostgreSQL schema is unavailable.")


def _create_user(role: str) -> int:
    suffix = uuid.uuid4().hex
    with _connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO app_user (name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            RETURNING id_user
            """,
            (f"Integration {role}", f"{suffix}@example.com", "test", role),
        )
        user_id = cursor.fetchone()["id_user"]
        if role == "TRAINER":
            cursor.execute(
                "INSERT INTO trainer (id_trainer) VALUES (%s)", (user_id,)
            )
    return user_id


def _create_group() -> int:
    with _connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO muscle_group (name) VALUES (%s) "
            "RETURNING id_muscle_group",
            (f"Integration group {uuid.uuid4().hex}",),
        )
        return cursor.fetchone()["id_muscle_group"]


def _cleanup(user_ids: list[int], group_ids: list[int]) -> None:
    with _connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM exercise WHERE id_trainer_creator = ANY(%s)",
            (user_ids,),
        )
        cursor.execute("DELETE FROM trainer WHERE id_trainer = ANY(%s)", (user_ids,))
        cursor.execute("DELETE FROM app_user WHERE id_user = ANY(%s)", (user_ids,))
        cursor.execute(
            "DELETE FROM muscle_group WHERE id_muscle_group = ANY(%s)",
            (group_ids,),
        )


def _payload(group_id: int, name: str) -> dict[str, object]:
    return {
        "name": name,
        "exercise_type": "strength",
        "intensity": "high",
        "muscle_group_id": group_id,
    }


def test_trainer_creation_and_duplicate_conflict(monkeypatch) -> None:
    trainer_id = _create_user("TRAINER")
    group_id = _create_group()
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEV_ACTOR_ID", str(trainer_id))
    monkeypatch.setenv("DEV_ACTOR_ROLE", "TRAINER")

    try:
        with TestClient(app) as client:
            first = client.post(
                "/api/v1/exercises", json=_payload(group_id, "Integration Press")
            )
            duplicate = client.post(
                "/api/v1/exercises", json=_payload(group_id, "  integration  press ")
            )

        assert first.status_code == 201
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "duplicate_resource"
    finally:
        _cleanup([trainer_id], [group_id])


def test_administrator_cannot_create_exercise(monkeypatch) -> None:
    admin_id = _create_user("ADMIN")
    group_id = _create_group()
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEV_ACTOR_ID", str(admin_id))
    monkeypatch.setenv("DEV_ACTOR_ROLE", "ADMIN")

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/exercises", json=_payload(group_id, "Forbidden Press")
            )

        assert response.status_code == 403
        assert response.json()["code"] == "permission_denied"
    finally:
        _cleanup([admin_id], [group_id])
