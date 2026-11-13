"""Domain contract for site persistence.

A gym site (branch/location) is the physical place where clients enroll and
train. Every client belongs to exactly one site, and site names must be unique
(U-3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.site import Site


class SiteRepository(ABC):
    """Persistence operations for gym sites."""

    @abstractmethod
    async def save(self, site: Site) -> Site:
        """Persist a new site and return it with its assigned identifier."""

    @abstractmethod
    async def get_by_id(self, id_site: int) -> Optional[Site]:
        """Return the site with that identifier, or ``None`` when it does not exist."""

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Site]:
        """Return the site with that name, or ``None`` when it does not exist."""

    @abstractmethod
    async def list(self) -> list[Site]:
        """Return every site, ordered by name."""

    @abstractmethod
    async def update(self, site: Site) -> Site:
        """Update an existing site and return the stored entity."""

    @abstractmethod
    async def deactivate(self, id_site: int) -> None:
        """Deactivate (logically remove) a site.

        Safe deactivation must not leave client records with invalid references.
        If clients are associated with the site, the operation is rejected.
        """
