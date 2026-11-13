"""Dependency providers for site management endpoints.

Wires the transaction manager, repository, and use cases together so FastAPI
endpoints can declare them with ``Depends``.
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from app.application.dto.actor import ActorDTO
from app.application.use_cases.create_site import CreateSiteUseCase
from app.application.use_cases.deactivate_site import DeactivateSiteUseCase
from app.application.use_cases.get_site import GetSiteUseCase
from app.application.use_cases.list_sites import ListSitesUseCase
from app.application.use_cases.update_site import UpdateSiteUseCase
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence.repositories.site_repository_sql import (
    SiteRepositorySql,
)
from app.infrastructure.persistence.transaction import PsqlTransactionManager

# A default actor used when no authentication layer is in place yet. All site
# management operations require administrator privileges, so the default actor
# is an administrator.
_DEFAULT_ACTOR = ActorDTO(id_user=1, role=UserRole.ADMIN)


async def get_transaction_manager() -> AsyncGenerator[PsqlTransactionManager, None]:
    """Yield a transaction manager bound to the current request."""
    tm = PsqlTransactionManager()
    async with tm:
        yield tm


async def get_site_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> AsyncGenerator[SiteRepositorySql, None]:
    """Yield a ``SiteRepositorySql`` using the given transaction manager."""
    yield SiteRepositorySql(tm)


async def get_create_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> AsyncGenerator[CreateSiteUseCase, None]:
    """Yield a ``CreateSiteUseCase`` using the given repository."""
    yield CreateSiteUseCase(repo)


async def get_get_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> AsyncGenerator[GetSiteUseCase, None]:
    """Yield a ``GetSiteUseCase`` using the given repository."""
    yield GetSiteUseCase(repo)


async def get_update_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> AsyncGenerator[UpdateSiteUseCase, None]:
    """Yield an ``UpdateSiteUseCase`` using the given repository."""
    yield UpdateSiteUseCase(repo)


async def get_deactivate_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> AsyncGenerator[DeactivateSiteUseCase, None]:
    """Yield a ``DeactivateSiteUseCase`` using the given repository."""
    yield DeactivateSiteUseCase(repo)


async def get_list_sites_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> AsyncGenerator[ListSitesUseCase, None]:
    """Yield a ``ListSitesUseCase`` using the given repository."""
    yield ListSitesUseCase(repo)


def _admin_actor() -> ActorDTO:
    """Return the default administrator actor (temporary, before auth layer)."""
    return _DEFAULT_ACTOR
