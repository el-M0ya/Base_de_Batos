"""Use case: list gym sites.

Any authenticated user can consult the list of sites.
"""

from __future__ import annotations

from app.application.dto.site_dto import ListSitesInputDTO, SiteOutputDTO
from app.domain.repositories.site_repository import SiteRepository


class ListSitesUseCase:
    """Return every site, ordered by name."""

    def __init__(self, site_repository: SiteRepository) -> None:
        self._sites = site_repository

    async def execute(self, input_dto: ListSitesInputDTO) -> tuple[SiteOutputDTO, ...]:
        sites = await self._sites.list()
        return tuple(SiteOutputDTO.from_entity(site) for site in sites)
