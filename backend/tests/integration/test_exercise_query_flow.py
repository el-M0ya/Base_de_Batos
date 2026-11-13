"""Integration tests for exercise persistence, filtering and ordering."""

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


def _seed() -> tuple[int, int, int]:
    suffix = uuid.uuid4().hex
    with _connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO app_user (name, email, password_hash, role)
            VALUES ('Integration Trainer', %s, 'test', 'TRAINER')
            RETURNING id_user
            """,
            (f"{suffix}@example.com",),
        )
        trainer_id = cursor.fetchone()["id_user"]
        cursor.execute("INSERT INTO trainer (id_trainer) VALUES (%s)", (trainer_id,))
        cursor.execute(
            "INSERT INTO muscle_group (name) VALUES (%s), (%s) "
            "RETURNING id_muscle_group",
            (f"Query group A {suffix}", f"Query group B {suffix}"),
        )
        groups = [row["id_muscle_group"] for row in cursor.fetchall()]
    return trainer_id, groups[0], groups[1]


def _cleanup(trainer_id: int, group_ids: tuple[int, int]) -> None:
    with _connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM exercise WHERE id_trainer_creator = %s", (trainer_id,)
        )
        cursor.execute("DELETE FROM trainer WHERE id_trainer = %s", (trainer_id,))
        cursor.execute("DELETE FROM app_user WHERE id_user = %s", (trainer_id,))
        cursor.execute(
            "DELETE FROM muscle_group WHERE id_muscle_group = ANY(%s)",
            (list(group_ids),),
        )


def _payload(group_id: int, name: str, exercise_type: str) -> dict[str, object]:
    return {
        "name": name,
        "exercise_type": exercise_type,
        "intensity": "high",
        "muscle_group_id": group_id,
    }


def test_listing_filters_and_same_name_in_another_group(monkeypatch) -> None:
    trainer_id, first_group, second_group = _seed()
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEV_ACTOR_ID", str(trainer_id))
    monkeypatch.setenv("DEV_ACTOR_ROLE", "TRAINER")

    try:
        with TestClient(app) as client:
            first = client.post(
                "/api/v1/exercises",
                json=_payload(first_group, "Shared Exercise", "strength"),
            )
            second = client.post(
                "/api/v1/exercises",
                json=_payload(second_group, "Shared Exercise", "cardio"),
            )
            filtered = client.get(
                "/api/v1/exercises",
                params={"muscle_group_id": first_group, "order_by": "name"},
            )

        assert first.status_code == 201
        assert second.status_code == 201
        assert filtered.status_code == 200
        assert [item["name"] for item in filtered.json()] == ["Shared Exercise"]
        assert filtered.json()[0]["muscle_group_id"] == first_group
    finally:
        _cleanup(trainer_id, (first_group, second_group))
