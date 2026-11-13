"""Unit tests for endpoint-level authentication and authorization guards."""

from __future__ import annotations

import unittest
from datetime import datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.adapters.dependencies import (
    get_create_site_use_case,
    get_current_actor,
    require_admin,
)
from app.application.dto.actor import ActorDTO
from app.application.dto.site_dto import SiteOutputDTO
from app.application.exceptions import InvalidToken
from app.domain.value_objects.user_role import UserRole
from app.main import app


class RequireAdminTests(unittest.TestCase):
    def test_administrator_is_allowed(self) -> None:
        actor = ActorDTO(id_user=1, role=UserRole.ADMIN)

        self.assertIs(require_admin(actor), actor)

    def test_trainer_is_denied(self) -> None:
        with self.assertRaises(HTTPException) as context:
            require_admin(ActorDTO(id_user=2, role=UserRole.TRAINER))

        self.assertEqual(context.exception.status_code, 403)

    def test_client_is_denied(self) -> None:
        with self.assertRaises(HTTPException) as context:
            require_admin(ActorDTO(id_user=3, role=UserRole.CLIENT))

        self.assertEqual(context.exception.status_code, 403)


class ProtectedEndpointTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_me_requires_a_bearer_token(self) -> None:
        client = TestClient(app)

        response = client.get("/api/v1/auth/me")

        self.assertEqual(response.status_code, 401)
        self.assertIn("Bearer", response.headers.get("www-authenticate", ""))

    def test_authorisations_endpoint_rejects_a_trainer(self) -> None:
        app.dependency_overrides[get_current_actor] = lambda: ActorDTO(
            id_user=2, role=UserRole.TRAINER
        )
        client = TestClient(app)

        response = client.get("/api/v1/authorisations")

        self.assertEqual(response.status_code, 403)

    def test_authorisations_endpoint_rejects_a_client(self) -> None:
        app.dependency_overrides[get_current_actor] = lambda: ActorDTO(
            id_user=3, role=UserRole.CLIENT
        )
        client = TestClient(app)

        response = client.get("/api/v1/authorisations")

        self.assertEqual(response.status_code, 403)

    def test_invalid_token_is_rejected_by_me(self) -> None:
        class _InvalidResolver:
            async def execute(self, token: str):
                raise InvalidToken()

        from app.adapters.dependencies import get_resolve_session_use_case

        app.dependency_overrides[get_resolve_session_use_case] = _InvalidResolver
        client = TestClient(app)

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        self.assertEqual(response.status_code, 401)


class ProtectedSiteEndpointTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_sites_endpoint_rejects_a_trainer(self) -> None:
        app.dependency_overrides[get_current_actor] = lambda: ActorDTO(
            id_user=2, role=UserRole.TRAINER
        )
        client = TestClient(app)

        response = client.get("/api/v1/sites")

        self.assertEqual(response.status_code, 403)

    def test_site_creation_reads_actor_from_token_not_from_body(self) -> None:
        received = {}

        class _CreateSite:
            async def execute(self, dto):
                received["actor"] = dto.actor
                return SiteOutputDTO(
                    id_site=10,
                    name=dto.name,
                    address=dto.address,
                    created_at=datetime(2026, 1, 1),
                )

        app.dependency_overrides[get_current_actor] = lambda: ActorDTO(
            id_user=7, role=UserRole.ADMIN
        )
        app.dependency_overrides[get_create_site_use_case] = lambda: _CreateSite()
        client = TestClient(app)

        response = client.post(
            "/api/v1/sites",
            json={"name": "Sede Centro", "address": "Calle 1"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(received["actor"].id_user, 7)
        self.assertEqual(received["actor"].role, UserRole.ADMIN)
