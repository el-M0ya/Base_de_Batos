"""Dependency providers for site and exercise-reclassification endpoints.

Wires the transaction manager, repositories, and use cases together so FastAPI
endpoints can declare them with ``Depends``.
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, Header

from app.adapters.routers._errors import to_http_exception
from app.application.dto.actor import ActorDTO
from app.application.dto.site_dto import (
    CreateSiteInputDTO,
    DeactivateSiteInputDTO,
    UpdateSiteInputDTO,
)
from app.application.exceptions import InvalidInput
from app.application.use_cases.create_site import CreateSiteUseCase
from app.application.use_cases.deactivate_site import DeactivateSiteUseCase
from app.application.use_cases.get_site import GetSiteUseCase
from app.application.use_cases.list_sites import ListSitesUseCase
from app.application.use_cases.reclassify_exercise import ReclassifyExerciseUseCase
from app.application.use_cases.update_site import UpdateSiteUseCase
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence.repositories.catalog_repository_sql import (
    CatalogRepositorySql,
)
from app.infrastructure.persistence.repositories.exercise_repository_sql import (
    ExerciseRepositorySql,
)
from app.infrastructure.persistence.repositories.site_repository_sql import (
    SiteRepositorySql,
)
from app.infrastructure.persistence.transaction import PsqlTransactionManager

# A default actor used when no authentication layer is in place yet. Site and
# catalog management operations require administrator privileges, so the
# default actor is an administrator.
_DEFAULT_ACTOR = ActorDTO(id_user=1, role=UserRole.ADMIN)


async def get_transaction_manager() -> AsyncGenerator[PsqlTransactionManager, None]:
    """Yield a transaction manager bound to the current request."""
    tm = PsqlTransactionManager()
    async with tm:
        yield tm


async def get_site_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> SiteRepositorySql:
    """Yield a ``SiteRepositorySql`` using the given transaction manager."""
    yield SiteRepositorySql(tm)


async def get_create_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> CreateSiteUseCase:
    """Yield a ``CreateSiteUseCase`` using the given repository."""
    yield CreateSiteUseCase(repo)


async def get_get_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> GetSiteUseCase:
    """Yield a ``GetSiteUseCase`` using the given repository."""
    yield GetSiteUseCase(repo)


async def get_update_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> UpdateSiteUseCase:
    """Yield an ``UpdateSiteUseCase`` using the given repository."""
    yield UpdateSiteUseCase(repo)


async def get_deactivate_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> DeactivateSiteUseCase:
    """Yield a ``DeactivateSiteUseCase`` using the given repository."""
    yield DeactivateSiteUseCase(repo)


async def get_list_sites_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> ListSitesUseCase:
    """Yield a ``ListSitesUseCase`` using the given repository."""
    yield ListSitesUseCase(repo)


# ---------------------------------------------------------------------------
# Exercise bank
# ---------------------------------------------------------------------------


async def get_exercise_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> AsyncGenerator[ExerciseRepositorySql, None]:
    """Yield an ``ExerciseRepositorySql`` using the given transaction manager."""
    yield ExerciseRepositorySql(tm)


async def get_catalog_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> AsyncGenerator[CatalogRepositorySql, None]:
    """Yield a ``CatalogRepositorySql`` using the given transaction manager."""
    yield CatalogRepositorySql(tm)


async def get_reclassify_exercise_use_case(
    exercises: ExerciseRepositorySql = Depends(get_exercise_repository),
    catalogs: CatalogRepositorySql = Depends(get_catalog_repository),
) -> AsyncGenerator[ReclassifyExerciseUseCase, None]:
    """Yield a ``ReclassifyExerciseUseCase`` with both repositories wired."""
    yield ReclassifyExerciseUseCase(exercises, catalogs)


async def get_actor(
    x_user_id: int = Header(default=1, alias="X-User-Id", ge=1),
    x_user_role: str = Header(default="TRAINER", alias="X-User-Role"),
) -> ActorDTO:
    """Return the authenticated actor from the provisional request headers.

    Authentication is not implemented yet (E2-08). Until then the exercise
    endpoint reads the actor from ``X-User-Id`` and ``X-User-Role`` so the
    authorization rules can be exercised without leaking a default admin actor
    into a trainer-only operation. The defaults keep local development usable.
    """
    try:
        return ActorDTO(
            id_user=x_user_id,
            role=UserRole.from_value(x_user_role),
        )
    except DomainException as error:
        raise to_http_exception(InvalidInput(str(error))) from error


def _admin_actor() -> ActorDTO:
    """Return the default administrator actor (temporary, before auth layer)."""
    return _DEFAULT_ACTOR
