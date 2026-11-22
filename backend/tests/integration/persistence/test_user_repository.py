"""Integration tests for the SQL user repository against a real PostgreSQL DB."""

from __future__ import annotations

import asyncio
import unittest

from psycopg import connect as _psycopg_connect

from backend.tests.integration.base import IntegrationTestCase
from backend.tests.integration.support.builders import build_site
from backend.tests.integration.support.database import _target_db_dsn
from app.domain.entities.client import Client
from app.domain.entities.trainer import Trainer
from app.domain.entities.user import User
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence.repositories.user_repository_sql import (
    UserRepositorySql,
)


class UserRepositorySqlIntegrationTests(IntegrationTestCase):
    """Tests for ``UserRepositorySql`` over a real PostgreSQL database."""

    def _repo(self, tm) -> UserRepositorySql:
        return UserRepositorySql(tm)

    # ------------------------------------------------------------------
    # Create and retrieve
    # ------------------------------------------------------------------

    def test_create_and_retrieve_admin(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                saved = await repo.save(
                    User(
                        name="Admin Uno",
                        email="admin.uno@example.com",
                        password_hash="hash",
                        role=UserRole.ADMIN,
                    )
                )
                self.assertIsNotNone(saved.id_user)
                self.assertTrue(saved.active)

                fetched = await repo.get_by_id(saved.id_user)
                self.assertIsNotNone(fetched)
                self.assertEqual(fetched.email, "admin.uno@example.com")
                self.assertEqual(fetched.role, UserRole.ADMIN)

        asyncio.run(scenario())

    def test_create_client_with_profile_in_same_transaction(self) -> None:
        async def scenario() -> None:
            site_id = build_site(
                name="Gimnasio Test", address="Calle Falsa 123"
            ).id_site
            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                saved = await repo.save(
                    User(
                        name="Cliente",
                        email="client@example.com",
                        password_hash="hash",
                        role=UserRole.CLIENT,
                    ),
                    profile=Client(
                        user=User(
                            name="Cliente",
                            email="client@example.com",
                            password_hash="hash",
                            role=UserRole.CLIENT,
                        ),
                        age=30,
                        id_site=site_id,
                    ),
                )
                self.assertIsNotNone(saved.id_user)

                profile = await repo.get_profile(saved.id_user)
                self.assertIsInstance(profile, Client)
                self.assertEqual(profile.age, 30)
                self.assertEqual(profile.id_site, site_id)

        asyncio.run(scenario())

    def test_create_trainer_with_profile_in_same_transaction(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                saved = await repo.save(
                    User(
                        name="Entrenador",
                        email="trainer@example.com",
                        password_hash="hash",
                        role=UserRole.TRAINER,
                    ),
                    profile=Trainer(
                        user=User(
                            name="Entrenador",
                            email="trainer@example.com",
                            password_hash="hash",
                            role=UserRole.TRAINER,
                        ),
                        specialty="CARDIO",
                    ),
                )
                self.assertIsNotNone(saved.id_user)

                profile = await repo.get_profile(saved.id_user)
                self.assertIsInstance(profile, Trainer)
                self.assertEqual(profile.specialty.value, "CARDIO")

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Uniqueness (U-1)
    # ------------------------------------------------------------------

    def test_duplicate_email_is_rejected(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                await repo.save(
                    User(
                        name="Primero",
                        email="dup@example.com",
                        password_hash="hash",
                        role=UserRole.ADMIN,
                    )
                )
                with self.assertRaises(Exception):
                    await repo.save(
                        User(
                            name="Segundo",
                            email="dup@example.com",
                            password_hash="hash",
                            role=UserRole.ADMIN,
                        )
                    )

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def test_list_users(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                await repo.save(
                    User(
                        name="Uno",
                        email="uno@example.com",
                        password_hash="hash",
                        role=UserRole.ADMIN,
                    )
                )
                await repo.save(
                    User(
                        name="Dos",
                        email="dos@example.com",
                        password_hash="hash",
                        role=UserRole.CLIENT,
                    )
                )
                users = await repo.list_users()
            self.assertGreaterEqual(len(users), 2)
            emails = {u.email for u in users}
            self.assertIn("uno@example.com", emails)
            self.assertIn("dos@example.com", emails)

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def test_update_user(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                saved = await repo.save(
                    User(
                        name="Original",
                        email="update@example.com",
                        password_hash="hash",
                        role=UserRole.TRAINER,
                    )
                )
                self.assertIsNotNone(saved.id_user)

                updated = await repo.update(
                    User(
                        id_user=saved.id_user,
                        name="Modificado",
                        email="update@example.com",
                        password_hash="hash",
                        role=UserRole.TRAINER,
                    )
                )
                self.assertEqual(updated.name, "Modificado")

                fetched = await repo.get_by_id(saved.id_user)
                self.assertEqual(fetched.name, "Modificado")

        asyncio.run(scenario())

    def test_update_nonexistent_user_raises(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                with self.assertRaises(Exception):
                    await repo.update(
                        User(
                            id_user=999999,
                            name="No existe",
                            email="nope@example.com",
                            password_hash="hash",
                            role=UserRole.ADMIN,
                        )
                    )

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Deactivation (logical, preserves history)
    # ------------------------------------------------------------------

    def test_deactivate_preserves_record(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                saved = await repo.save(
                    User(
                        name="Baja",
                        email="deactivate@example.com",
                        password_hash="hash",
                        role=UserRole.CLIENT,
                    )
                )
                self.assertIsNotNone(saved.id_user)

                deactivated = await repo.deactivate(saved.id_user)
                self.assertFalse(deactivated.active)

                fetched = await repo.get_by_id(saved.id_user)
                self.assertIsNotNone(fetched)
                self.assertFalse(fetched.active)

        asyncio.run(scenario())

    def test_deactivate_nonexistent_user_raises(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                with self.assertRaises(Exception):
                    await repo.deactivate(999999)

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Profile reads (specialization consistency)
    # ------------------------------------------------------------------

    def test_get_profile_trainer(self) -> None:
        async def scenario() -> None:
            conn = _psycopg_connect(_target_db_dsn(), autocommit=True)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO app_user (name, email, password_hash, role, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id_user
                        """,
                        ("T", "t.profile@example.com", "hash", "TRAINER", True),
                    )
                    user_id = cur.fetchone()[0]
                    cur.execute(
                        "INSERT INTO trainer (id_trainer, specialty) VALUES (%s, %s)",
                        (user_id, "CARDIO"),
                    )
            finally:
                conn.close()

            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                profile = await repo.get_profile(user_id)

            self.assertIsInstance(profile, Trainer)
            self.assertEqual(profile.specialty.value, "CARDIO")

        asyncio.run(scenario())

    def test_get_profile_client_requires_site(self) -> None:
        async def scenario() -> None:
            site_id = build_site(
                name="Gimnasio Test", address="Calle Falsa 123"
            ).id_site
            conn = _psycopg_connect(_target_db_dsn(), autocommit=True)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO app_user (name, email, password_hash, role, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id_user
                        """,
                        ("C", "c.profile@example.com", "hash", "CLIENT", True),
                    )
                    user_id = cur.fetchone()[0]
                    cur.execute(
                        "INSERT INTO client (id_client, age, id_site) VALUES (%s, %s, %s)",
                        (user_id, 30, site_id),
                    )
            finally:
                conn.close()

            async with self.transaction_manager() as tm:
                repo = self._repo(tm)
                profile = await repo.get_profile(user_id)

            self.assertIsInstance(profile, Client)
            self.assertEqual(profile.age, 30)
            self.assertEqual(profile.id_site, site_id)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
