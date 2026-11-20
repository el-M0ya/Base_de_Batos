"""Use case: update an existing gym site.

Only administrators may update sites. The new name must remain unique (U-3).
"""

from __future__ import annotations

from app.application.dto.site_dto import SiteOutputDTO, UpdateSiteInputDTO
from app.application.exceptions import (
    DuplicateResource,
    PermissionDenied,
    ResourceNotFound,
)
from app.domain.entities.site import Site
from app.domain.repositories.site_repository import SiteRepository
from app.domain.value_objects.user_role import UserRole


class UpdateSiteUseCase:
    """Update the name and/or address of an existing site."""

    def __init__(self, site_repository: SiteRepository) -> None:
        self._sites = site_repository

    async def execute(self, input_dto: UpdateSiteInputDTO) -> SiteOutputDTO:
        actor = input_dto.actor
        if actor.role is not UserRole.ADMIN:
            raise PermissionDenied(
                "only administrators can update sites; "
                f"the actor has the role {actor.role.value}."
            )

        site = await self._sites.get_by_id(input_dto.id_site)
        if site is None:
            raise ResourceNotFound("site", input_dto.id_site)

        if input_dto.name is not None:
            existing = await self._sites.get_by_name(input_dto.name.strip())
            if existing is not None and existing.id_site != input_dto.id_site:
                raise DuplicateResource(
                    "site",
                    f"a site with the name {input_dto.name!r} already exists "
                    f"(id_site={existing.id_site}).",
                )
            site.name = input_dto.name.strip()

        if input_dto.address is not None:
            site.address = input_dto.address.strip()

        saved = await self._sites.update(site)
        return SiteOutputDTO.from_entity(saved)
