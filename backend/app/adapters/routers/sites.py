"""FastAPI router for site management endpoints.

Provides REST endpoints to create, retrieve, update, list, and deactivate gym
sites. Site names are unique (U-3) and deactivation is safe: it is rejected when
clients are associated with the site.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.adapters.dependencies import (
    get_create_site_use_case,
    get_deactivate_site_use_case,
    get_get_site_use_case,
    get_list_sites_use_case,
    get_update_site_use_case,
)
from app.application.dto.actor import ActorDTO
from app.application.dto.site_dto import (
    CreateSiteInputDTO,
    DeactivateSiteInputDTO,
    SiteOutputDTO,
    UpdateSiteInputDTO,
)
from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    PermissionDenied,
    ResourceNotFound,
)
from app.adapters.dependencies import _admin_actor

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post(
    "",
    response_model=SiteOutputDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a gym site",
)
async def create_site(
    input_dto: CreateSiteInputDTO,
    use_case=Depends(get_create_site_use_case),
) -> SiteOutputDTO:
    """Register a new gym site. Only administrators may create sites."""
    actor = _admin_actor()
    create_dto = CreateSiteInputDTO(
        actor=actor,
        name=input_dto.name,
        address=input_dto.address,
    )
    try:
        return await use_case.execute(create_dto)
    except DuplicateResource as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error.detail,
        ) from error
    except PermissionDenied as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error.detail,
        ) from error


@router.get(
    "/{id_site}",
    response_model=SiteOutputDTO,
    summary="Get a site by identifier",
)
async def get_site(
    id_site: int = Path(..., ge=1),
    use_case=Depends(get_get_site_use_case),
) -> SiteOutputDTO:
    """Return the site with the given identifier."""
    try:
        return await use_case.execute(id_site)
    except ResourceNotFound as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[SiteOutputDTO],
    summary="List all sites",
)
async def list_sites(
    use_case=Depends(get_list_sites_use_case),
) -> list[SiteOutputDTO]:
    """Return every site, ordered by name."""
    actor = _admin_actor()
    from app.application.dto.site_dto import ListSitesInputDTO

    list_dto = ListSitesInputDTO(actor=actor)
    return await use_case.execute(list_dto)


@router.put(
    "/{id_site}",
    response_model=SiteOutputDTO,
    summary="Update a site",
)
async def update_site(
    input_dto: UpdateSiteInputDTO,
    id_site: int = Path(..., ge=1),
    use_case=Depends(get_update_site_use_case),
) -> SiteOutputDTO:
    """Update the name and/or address of an existing site."""
    actor = _admin_actor()
    update_dto = UpdateSiteInputDTO(
        actor=actor,
        id_site=id_site,
        name=input_dto.name,
        address=input_dto.address,
    )
    try:
        return await use_case.execute(update_dto)
    except ResourceNotFound as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except DuplicateResource as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error.detail,
        ) from error
    except PermissionDenied as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error.detail,
        ) from error


@router.delete(
    "/{id_site}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a site",
)
async def deactivate_site(
    id_site: int = Path(..., ge=1),
    use_case=Depends(get_deactivate_site_use_case),
) -> None:
    """Deactivate a site. Rejected when clients are associated with it."""
    actor = _admin_actor()
    deactivate_dto = DeactivateSiteInputDTO(actor=actor, id_site=id_site)
    try:
        await use_case.execute(deactivate_dto)
    except ResourceNotFound as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except BusinessRuleViolation as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error.detail,
        ) from error
    except PermissionDenied as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error.detail,
        ) from error
