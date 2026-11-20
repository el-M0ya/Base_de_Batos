"""Use case: retrieve a gym site by identifier.

Any authenticated user can consult a site.
"""

from __future__ import annotations

from app.application.dto.site_dto import SiteOutputDTO
from app.application.exceptions import ResourceNotFound
from app.domain.repositories.site_repository import SiteRepository


class GetSiteUseCase:
    """Return the site with the given identifier, or raise if missing."""

    def __init__(self, site_repository: SiteRepository) -> None:
        self._sites = site_repository

    async def execute(self, id_site: int) -> SiteOutputDTO:
        site = await self._sites.get_by_id(id_site)
        if site is None:
            raise ResourceNotFound("site", id_site)
        return SiteOutputDTO.from_entity(site)
