"""Unit tests for the site management use cases.

Uses an in-memory repository so no database is required.
"""

from __future__ import annotations

import unittest
from datetime import datetime

from app.application.dto.actor import ActorDTO
from app.application.dto.site_dto import (
    CreateSiteInputDTO,
    DeactivateSiteInputDTO,
    ListSitesInputDTO,
    UpdateSiteInputDTO,
)
from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    PermissionDenied,
    ResourceNotFound,
)
from app.application.use_cases.create_site import CreateSiteUseCase
from app.application.use_cases.deactivate_site import DeactivateSiteUseCase
from app.application.use_cases.get_site import GetSiteUseCase
from app.application.use_cases.list_sites import ListSitesUseCase
from app.application.use_cases.update_site import UpdateSiteUseCase
from app.domain.entities.site import Site
from app.domain.repositories.site_repository import SiteRepository
from app.domain.value_objects.user_role import UserRole


class InMemorySiteRepository(SiteRepository):
    """Dictionary-backed site repository for unit tests."""

    def __init__(self, sites: list[Site] | None = None) -> None:
        self._sites: dict[int, Site] = {}
        self._next_id = 1
        for site in sites or []:
            self._save_sync(site)

    def _save_sync(self, site: Site) -> Site:
        if site.id_site is None:
            saved = Site(
                name=site.name,
                address=site.address,
                id_site=self._next_id,
                created_at=site.created_at or datetime(2026, 1, 1),
            )
            self._next_id += 1
        else:
            saved = site
            self._next_id = max(self._next_id, saved.id_site + 1)
        self._sites[saved.id_site] = saved
        return saved

    async def save(self, site: Site) -> Site:
        return self._save_sync(site)

    async def get_by_id(self, id_site: int) -> Site | None:
        return self._sites.get(id_site)

    async def get_by_name(self, name: str) -> Site | None:
        for site in self._sites.values():
            if site.name == name:
                return site
        return None

    async def list(self) -> list[Site]:
        return sorted(self._sites.values(), key=lambda s: s.name)

    async def update(self, site: Site) -> Site:
        if site.id_site not in self._sites:
            raise ResourceNotFound("site", site.id_site)
        self._sites[site.id_site] = site
        return site

    async def deactivate(self, id_site: int) -> None:
        if id_site not in self._sites:
            raise ResourceNotFound("site", id_site)
        # Simulate clients associated: block deactivation for id_site == 1
        if id_site == 1:
            raise BusinessRuleViolation(
                "the site cannot be removed because clients are associated with it"
            )
        del self._sites[id_site]


class CreateSiteUseCaseTests(unittest.TestCase):
    """Tests for :class:`CreateSiteUseCase`."""

    def setUp(self) -> None:
        self.repo = InMemorySiteRepository()
        self.use_case = CreateSiteUseCase(self.repo)
        self.admin = ActorDTO(id_user=1, role=UserRole.ADMIN)
        self.trainer = ActorDTO(id_user=2, role=UserRole.TRAINER)

    def test_create_site_as_admin(self) -> None:
        dto = CreateSiteInputDTO(
            actor=self.admin, name="Gimnasio Centro", address="Av. Central 123"
        )
        saved = self.use_case.execute.__wrapped__ if hasattr(
            self.use_case.execute, "__wrapped__"
        ) else None
        # execute is async; run it
        import asyncio

        result = asyncio.run(self.use_case.execute(dto))
        self.assertIsNotNone(result.id_site)
        self.assertEqual(result.name, "Gimnasio Centro")

    def test_duplicate_name_is_rejected(self) -> None:
        import asyncio

        asyncio.run(
            self.use_case.execute(
                CreateSiteInputDTO(
                    actor=self.admin, name="Duplicado", address="Dir 1"
                )
            )
        )
        with self.assertRaises(DuplicateResource):
            asyncio.run(
                self.use_case.execute(
                    CreateSiteInputDTO(
                        actor=self.admin, name="Duplicado", address="Dir 2"
                    )
                )
            )

    def test_non_admin_cannot_create(self) -> None:
        import asyncio

        with self.assertRaises(PermissionDenied):
            asyncio.run(
                self.use_case.execute(
                    CreateSiteInputDTO(
                        actor=self.trainer, name="Gimnasio", address="Dir"
                    )
                )
            )


class GetSiteUseCaseTests(unittest.TestCase):
    """Tests for :class:`GetSiteUseCase`."""

    def setUp(self) -> None:
        self.repo = InMemorySiteRepository(
            [Site(id_site=10, name="Sitio 10", address="Dir 10")]
        )
        self.use_case = GetSiteUseCase(self.repo)

    def test_get_existing_site(self) -> None:
        import asyncio

        result = asyncio.run(self.use_case.execute(10))
        self.assertEqual(result.id_site, 10)
        self.assertEqual(result.name, "Sitio 10")

    def test_get_missing_site_raises(self) -> None:
        import asyncio

        with self.assertRaises(ResourceNotFound):
            asyncio.run(self.use_case.execute(99999))


class UpdateSiteUseCaseTests(unittest.TestCase):
    """Tests for :class:`UpdateSiteUseCase`."""

    def setUp(self) -> None:
        self.repo = InMemorySiteRepository(
            [Site(id_site=10, name="Viejo", address="Dir Vieja")]
        )
        self.use_case = UpdateSiteUseCase(self.repo)
        self.admin = ActorDTO(id_user=1, role=UserRole.ADMIN)

    def test_update_site(self) -> None:
        import asyncio

        result = asyncio.run(
            self.use_case.execute(
                UpdateSiteInputDTO(
                    actor=self.admin, id_site=10, name="Nuevo", address="Dir Nueva"
                )
            )
        )
        self.assertEqual(result.name, "Nuevo")
        self.assertEqual(result.address, "Dir Nueva")

    def test_duplicate_name_on_update_is_rejected(self) -> None:
        import asyncio

        # Create a second site
        asyncio.run(
            self.repo.save(Site(id_site=11, name="Otro", address="Dir Otro"))
        )
        with self.assertRaises(DuplicateResource):
            asyncio.run(
                self.use_case.execute(
                    UpdateSiteInputDTO(
                        actor=self.admin, id_site=10, name="Otro", address="Dir"
                    )
                )
            )


class DeactivateSiteUseCaseTests(unittest.TestCase):
    """Tests for :class:`DeactivateSiteUseCase`."""

    def setUp(self) -> None:
        self.repo = InMemorySiteRepository(
            [
                Site(id_site=1, name="Con Clientes", address="Dir 1"),
                Site(id_site=2, name="Sin Clientes", address="Dir 2"),
            ]
        )
        self.use_case = DeactivateSiteUseCase(self.repo)
        self.admin = ActorDTO(id_user=1, role=UserRole.ADMIN)

    def test_deactivate_site_without_clients(self) -> None:
        import asyncio

        asyncio.run(
            self.use_case.execute(
                DeactivateSiteInputDTO(actor=self.admin, id_site=2)
            )
        )
        self.assertIsNone(asyncio.run(self.repo.get_by_id(2)))

    def test_deactivate_site_with_clients_is_rejected(self) -> None:
        import asyncio

        with self.assertRaises(BusinessRuleViolation):
            asyncio.run(
                self.use_case.execute(
                    DeactivateSiteInputDTO(actor=self.admin, id_site=1)
                )
            )
        # Site should still exist
        self.assertIsNotNone(asyncio.run(self.repo.get_by_id(1)))

    def test_deactivate_nonexistent_site_raises(self) -> None:
        import asyncio

        with self.assertRaises(ResourceNotFound):
            asyncio.run(
                self.use_case.execute(
                    DeactivateSiteInputDTO(actor=self.admin, id_site=99999)
                )
            )


class ListSitesUseCaseTests(unittest.TestCase):
    """Tests for :class:`ListSitesUseCase`."""

    def setUp(self) -> None:
        self.repo = InMemorySiteRepository(
            [
                Site(id_site=1, name="Zona Gym", address="Zona"),
                Site(id_site=2, name="Alpha Fitness", address="Alpha"),
                Site(id_site=3, name="Beta Club", address="Beta"),
            ]
        )
        self.use_case = ListSitesUseCase(self.repo)
        self.admin = ActorDTO(id_user=1, role=UserRole.ADMIN)

    def test_list_sites_ordered_by_name(self) -> None:
        import asyncio

        result = asyncio.run(
            self.use_case.execute(ListSitesInputDTO(actor=self.admin))
        )
        names = [s.name for s in result]
        self.assertEqual(names, ["Alpha Fitness", "Beta Club", "Zona Gym"])


if __name__ == "__main__":
    unittest.main()
