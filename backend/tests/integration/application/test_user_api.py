"""Integration tests for the administrator-managed users HTTP API."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.adapters.dependencies import get_current_actor, get_user_repository
from app.application.dto.actor import ActorDTO
from app.application.dto.user_dto import (
    ClientProfileInputDTO,
    TrainerProfileInputDTO,
)
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.user_role import UserRole
from app.main import app
from backend.tests.unit.application.fakes.in_memory_user_repository import (
    InMemoryUserRepository,
)


class _AdminActor:
    """Override that forces every request to be performed by an administrator."""

    def __call__(self) -> ActorDTO:
        return ActorDTO(id_user=1, role=UserRole.ADMIN)


class _TrainerActor:
    """Override that forces every request to be performed by a trainer."""

    def __call__(self) -> ActorDTO:
        return ActorDTO(id_user=2, role=UserRole.TRAINER)


class UserApiIntegrationTests(unittest.TestCase):
    """Tests for the ``/api/v1/users`` endpoints through FastAPI's TestClient."""

    def setUp(self) -> None:
        self.repository = InMemoryUserRepository()
        self.client = TestClient(app)
        app.dependency_overrides[get_current_actor] = _AdminActor()
        app.dependency_overrides[get_user_repository] = lambda: self.repository

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def _post(self, payload: dict):
        return self.client.post("/api/v1/users", json=payload)

    def _patch(self, id_user: int, payload: dict):
        return self.client.patch(f"/api/v1/users/{id_user}", json=payload)

    def _delete(self, id_user: int):
        return self.client.delete(f"/api/v1/users/{id_user}")

    def test_admin_creates_trainer_with_profile(self) -> None:
        response = self._post(
            {
                "name": "Entrenador",
                "email": "trainer@example.com",
                "password": "Password123",
                "role": "TRAINER",
                "trainer": {"specialty": "CARDIO"},
            }
        )
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        self.assertEqual(body["email"], "trainer@example.com")
        self.assertEqual(body["role"], "TRAINER")
        self.assertTrue(body["active"])
        self.assertIsNotNone(body["trainer"])
        self.assertEqual(body["trainer"]["specialty"], "CARDIO")
        self.assertIsNone(body["client"])

    def test_admin_creates_client_with_profile(self) -> None:
        response = self._post(
            {
                "name": "Cliente",
                "email": "client@example.com",
                "password": "Password123",
                "role": "CLIENT",
                "client": {"age": 30, "id_site": 1},
            }
        )
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        self.assertEqual(body["role"], "CLIENT")
        self.assertIsNotNone(body["client"])
        self.assertEqual(body["client"]["age"], 30)
        self.assertEqual(body["client"]["id_site"], 1)
        self.assertIsNone(body["trainer"])

    def test_create_duplicate_email_is_rejected(self) -> None:
        self._post(
            {
                "name": "Primero",
                "email": "dup@example.com",
                "password": "Password123",
                "role": "ADMIN",
            }
        )
        response = self._post(
            {
                "name": "Segundo",
                "email": "dup@example.com",
                "password": "Password123",
                "role": "ADMIN",
            }
        )
        self.assertEqual(response.status_code, 409, response.text)

    def test_trainer_cannot_manage_users(self) -> None:
        app.dependency_overrides[get_current_actor] = _TrainerActor()
        try:
            response = self._post(
                {
                    "name": "Intruso",
                    "email": "intruso@example.com",
                    "password": "Password123",
                    "role": "ADMIN",
                }
            )
            self.assertEqual(response.status_code, 403, response.text)
        finally:
            app.dependency_overrides[get_current_actor] = _AdminActor()

    def test_list_users(self) -> None:
        self._post(
            {
                "name": "Cliente",
                "email": "list@example.com",
                "password": "Password123",
                "role": "CLIENT",
                "client": {"age": 25, "id_site": 1},
            }
        )
        response = self.client.get("/api/v1/users")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertGreaterEqual(len(body), 1)
        emails = {item["email"] for item in body}
        self.assertIn("list@example.com", emails)

    def test_get_user_by_id(self) -> None:
        create = self._post(
            {
                "name": "Recuperar",
                "email": "get@example.com",
                "password": "Password123",
                "role": "TRAINER",
                "trainer": {"specialty": "GENERAL"},
            }
        )
        user_id = create.json()["id_user"]
        response = self.client.get(f"/api/v1/users/{user_id}")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["id_user"], user_id)
        self.assertEqual(body["email"], "get@example.com")

    def test_get_missing_user_returns_404(self) -> None:
        response = self.client.get("/api/v1/users/999999")
        self.assertEqual(response.status_code, 404, response.text)

    def test_update_user(self) -> None:
        create = self._post(
            {
                "name": "Antes",
                "email": "update@example.com",
                "password": "Password123",
                "role": "CLIENT",
                "client": {"age": 30, "id_site": 1},
            }
        )
        user_id = create.json()["id_user"]
        response = self._patch(
            user_id,
            {"name": "Después", "client": {"age": 31, "id_site": 1}},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["name"], "Después")
        self.assertEqual(body["client"]["age"], 31)

    def test_deactivate_user_preserves_record(self) -> None:
        create = self._post(
            {
                "name": "Baja",
                "email": "deactivate@example.com",
                "password": "Password123",
                "role": "CLIENT",
                "client": {"age": 30, "id_site": 1},
            }
        )
        user_id = create.json()["id_user"]
        response = self._delete(user_id)
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertFalse(body["active"])
        # The account must still be retrievable (logical deletion).
        get_response = self.client.get(f"/api/v1/users/{user_id}")
        self.assertEqual(get_response.status_code, 200, get_response.text)
        self.assertFalse(get_response.json()["active"])

    def test_create_missing_required_fields_is_rejected(self) -> None:
        response = self._post(
            {
                "name": "",
                "email": "nope@example.com",
                "password": "Password123",
                "role": "ADMIN",
            }
        )
        self.assertEqual(response.status_code, 422, response.text)

    def test_client_age_must_be_positive_and_in_range(self) -> None:
        response = self._post(
            {
                "name": "Cliente",
                "email": "age@example.com",
                "password": "Password123",
                "role": "CLIENT",
                "client": {"age": 10, "id_site": 1},
            }
        )
        self.assertEqual(response.status_code, 422, response.text)


if __name__ == "__main__":
    unittest.main()
