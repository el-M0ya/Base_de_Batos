"""Use case: create a gym site.

Only authorized actors may create sites. Site names must be unique (U-3).
"""

from __future__ import annotations

from app.application.dto.site_dto import CreateSiteInputDTO, SiteOutputDTO
from app.application.exceptions import DuplicateResource, PermissionDenied
from app.domain.entities.site import Site
from app.domain.repositories.site_repository import SiteRepository
from app.domain.value_objects.user_role import UserRole


class CreateSiteUseCase:
    """Register a new gym site."""

    def __init__(self, site_repository: SiteRepository) -> None:
        self._sites = site_repository

    async def execute(self, input_dto: CreateSiteInputDTO) -> SiteOutputDTO:
        actor = input_dto.actor
        if actor.role is not UserRole.ADMIN:
            raise PermissionDenied(
                "only administrators can create sites; "
                f"the actor has the role {actor.role.value}."
            )

        existing = await self._sites.get_by_name(input_dto.name.strip())
        if existing is not None:
            raise DuplicateResource(
                "site",
                f"a site with the name {input_dto.name!r} already exists "
                f"(id_site={existing.id_site}).",
            )

        site = Site(
            name=input_dto.name.strip(),
            address=input_dto.address.strip(),
        )
        saved = await self._sites.save(site)
        return SiteOutputDTO.from_entity(saved)
