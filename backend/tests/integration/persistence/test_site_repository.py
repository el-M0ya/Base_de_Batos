"""Integration tests for the SQL site repository.

Covers: create, retrieve, update, list, unique name constraint (U-3), safe
deactivation when clients are associated, and retrieval by primary key.
"""

from __future__ import annotations

import asyncio
import unittest
from datetime import date
from decimal import Decimal
from psycopg import connect as _psycopg_connect

from backend.tests.integration.base import IntegrationTestCase
from backend.tests.integration.support.builders import (
    build_muscle_group,
    build_trainer,
    build_user,
    build_workout_program,
)
from backend.tests.integration.support.database import _target_db_dsn
from app.domain.entities.site import Site
from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.entities.routine_parameters import RoutineParameters
from app.domain.entities.routine_structure import (
    BlockType,
    RoutineBlock,
    RoutineStructure,
)
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.infrastructure.persistence.repositories.site_repository_sql import (
    SiteRepositorySql,
)


def _save_site_direct(id_site: int, name: str, address: str) -> None:
    """Insert a site directly into the database (integration test helper)."""
    conn = _psycopg_connect(_target_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO site (id_site, name, address) VALUES (%s, %s, %s)",
                (id_site, name, address),
            )
    finally:
        conn.close()


def _count_rows(table: str) -> int:
    conn = _psycopg_connect(_target_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            return cur.fetchone()[0]
    finally:
        conn.close()


def _count_clients_for_site(id_site: int) -> int:
    conn = _psycopg_connect(_target_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM client WHERE id_site = %s", (id_site,))
            return cur.fetchone()[0]
    finally:
        conn.close()


class SiteRepositorySqlIntegrationTests(IntegrationTestCase):
    """Tests for :class:`SiteRepositorySql`."""

    def _site_repo(self, tm) -> SiteRepositorySql:
        return SiteRepositorySql(tm)

    # ------------------------------------------------------------------
    # Create and retrieve
    # ------------------------------------------------------------------

    def test_create_and_get_by_id(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                saved = await repo.save(
                    Site(name="Gimnasio Central", address="Av. Siempre Viva 123")
                )
                self.assertIsNotNone(saved.id_site)
                self.assertEqual(saved.name, "Gimnasio Central")
                self.assertEqual(saved.address, "Av. Siempre Viva 123")

                fetched = await repo.get_by_id(saved.id_site)
                self.assertIsNotNone(fetched)
                self.assertEqual(fetched.id_site, saved.id_site)
                self.assertEqual(fetched.name, "Gimnasio Central")

        asyncio.run(scenario())

    def test_get_by_id_not_found_returns_none(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                result = await repo.get_by_id(999999)
                self.assertIsNone(result)

        asyncio.run(scenario())

    def test_get_by_name(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                saved = await repo.save(
                    Site(name="Gimnasio Norte", address="Calle Falsa 123")
                )

                fetched = await repo.get_by_name("Gimnasio Norte")
                self.assertIsNotNone(fetched)
                self.assertEqual(fetched.id_site, saved.id_site)

                missing = await repo.get_by_name("Gimnasio Inexistente")
                self.assertIsNone(missing)

        asyncio.run(scenario())

    def test_list_sites_ordered_by_name(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                await repo.save(Site(name="Zona Gimnasio", address="Zona 1"))
                await repo.save(Site(name="Alpha Gym", address="Zona 2"))
                await repo.save(Site(name="Beta Fitness", address="Zona 3"))

                sites = await repo.list()
                self.assertEqual(len(sites), 3)
                self.assertEqual(sites[0].name, "Alpha Gym")
                self.assertEqual(sites[1].name, "Beta Fitness")
                self.assertEqual(sites[2].name, "Zona Gimnasio")

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def test_update_site(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                saved = await repo.save(
                    Site(name="Gimnasio Viejo", address="Direccion Vieja")
                )

                saved.name = "Gimnasio Nuevo"
                saved.address = "Direccion Nueva"
                updated = await repo.update(saved)
                self.assertEqual(updated.name, "Gimnasio Nuevo")
                self.assertEqual(updated.address, "Direccion Nueva")

                fetched = await repo.get_by_id(saved.id_site)
                self.assertEqual(fetched.name, "Gimnasio Nuevo")

        asyncio.run(scenario())

    def test_update_nonexistent_site_raises(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                site = Site(id_site=99999, name="No existe", address="Nunca")
                with self.assertRaises(Exception):
                    await repo.update(site)

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Unique name (U-3)
    # ------------------------------------------------------------------

    def test_duplicate_site_name_is_rejected(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                await repo.save(Site(name="Gimnasio Duplicado", address="Dir 1"))

                with self.assertRaises(Exception):
                    await repo.save(Site(name="Gimnasio Duplicado", address="Dir 2"))

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Safe deactivation
    # ------------------------------------------------------------------

    def test_deactivate_site_without_clients(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                saved = await repo.save(
                    Site(name="Sitio Sin Clientes", address="Dir Sin Clientes")
                )

                await repo.deactivate(saved.id_site)

                fetched = await repo.get_by_id(saved.id_site)
                self.assertIsNone(fetched)

        asyncio.run(scenario())

    def test_deactivate_site_with_clients_is_rejected(self) -> None:
        # Setup: create a trainer and a client associated to a site
        trainer_user = None  # placeholder, will be set below
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                site = await repo.save(
                    Site(name="Sitio Con Clientes", address="Dir Con Clientes")
                )

                # Insert a client associated to this site directly
                conn = _psycopg_connect(_target_db_dsn(), autocommit=True)
                try:
                    with conn.cursor() as cur:
                        # Need a user with role CLIENT first
                        cur.execute(
                            "INSERT INTO app_user (name, email, password_hash, role) VALUES (%s, %s, %s, %s) RETURNING id_user",
                            ("Cliente Test", "cliente@test.com", "hash", "CLIENT"),
                        )
                        id_user = cur.fetchone()[0]
                        cur.execute(
                            "INSERT INTO client (id_client, age, id_site) VALUES (%s, %s, %s)",
                            (id_user, 30, site.id_site),
                        )
                finally:
                    conn.close()

                with self.assertRaises(Exception):
                    await repo.deactivate(site.id_site)

                # Site should still exist
                fetched = await repo.get_by_id(site.id_site)
                self.assertIsNotNone(fetched)

        asyncio.run(scenario())

    def test_deactivate_nonexistent_site_raises(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                with self.assertRaises(Exception):
                    await repo.deactivate(999999)

        asyncio.run(scenario())

    # ------------------------------------------------------------------
    # Retrieval by primary key
    # ------------------------------------------------------------------

    def test_get_by_id_uses_primary_key_lookup(self) -> None:
        async def scenario() -> None:
            async with self.transaction_manager() as tm:
                repo = self._site_repo(tm)
                saved = await repo.save(
                    Site(name="Sitio PK", address="Dir PK")
                )

                fetched = await repo.get_by_id(saved.id_site)
                self.assertIsNotNone(fetched)
                self.assertEqual(fetched.id_site, saved.id_site)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
