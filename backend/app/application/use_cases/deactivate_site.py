"""Use case: deactivate a gym site.

Only administrators may deactivate sites. Deactivation is rejected when clients
are associated with the site, so existing client records never end with an
invalid site reference.
"""

from __future__ import annotations

from app.application.dto.site_dto import DeactivateSiteInputDTO
from app.application.exceptions import (
    BusinessRuleViolation,
    PermissionDenied,
    ResourceNotFound,
)
from app.domain.repositories.site_repository import SiteRepository
from app.domain.value_objects.user_role import UserRole


class DeactivateSiteUseCase:
    """Deactivate (logically remove) an existing site.

    The operation fails when clients reference the site, preserving
    referential integrity of historical records.
    """

    def __init__(self, site_repository: SiteRepository) -> None:
        self._sites = site_repository

    async def execute(self, input_dto: DeactivateSiteInputDTO) -> None:
        actor = input_dto.actor
        if actor.role is not UserRole.ADMIN:
            raise PermissionDenied(
                "only administrators can deactivate sites; "
                f"the actor has the role {actor.role.value}."
            )

        site = await self._sites.get_by_id(input_dto.id_site)
        if site is None:
            raise ResourceNotFound("site", input_dto.id_site)

        await self._sites.deactivate(input_dto.id_site)
