"""FastAPI router for site management endpoints.

Provides REST endpoints to create, retrieve, update, list, and deactivate gym
sites. Site names are unique (U-3) and deactivation is safe: it is rejected when
clients are associated with the site.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.adapters.dependencies import (
    get_create_site_use_case,
    get_deactivate_site_use_case,
    get_get_site_use_case,
    get_list_sites_use_case,
    get_update_site_use_case,
    require_admin,
)
from app.application.dto.actor import ActorDTO
from app.application.dto.site_dto import (
    CreateSiteInputDTO,
    DeactivateSiteInputDTO,
    ListSitesInputDTO,
    SiteOutputDTO,
    UpdateSiteInputDTO,
)
from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    PermissionDenied,
    ResourceNotFound,
)

router = APIRouter(prefix="/sites", tags=["sites"])


class CreateSiteRequest(BaseModel):
    """HTTP body for site creation; the actor comes from the bearer token."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    address: str = Field(min_length=1, max_length=255)


class UpdateSiteRequest(BaseModel):
    """HTTP body for site updates; the actor comes from the bearer token."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    address: Optional[str] = Field(default=None, min_length=1, max_length=255)

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "UpdateSiteRequest":
        if self.name is None and self.address is None:
            raise ValueError("At least one of name or address must be provided.")
        return self


@router.post(
    "",
    response_model=SiteOutputDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a gym site",
)
async def create_site(
    request: CreateSiteRequest,
    actor: ActorDTO = Depends(require_admin),
    use_case=Depends(get_create_site_use_case),
) -> SiteOutputDTO:
    """Register a new gym site. Only administrators may create sites."""
    create_dto = CreateSiteInputDTO(
        actor=actor,
        name=request.name,
        address=request.address,
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
    _actor: ActorDTO = Depends(require_admin),
    use_case=Depends(get_get_site_use_case),
) -> SiteOutputDTO:
    """Return the site with the given identifier. Administrators only."""
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
    actor: ActorDTO = Depends(require_admin),
    use_case=Depends(get_list_sites_use_case),
) -> list[SiteOutputDTO]:
    """Return every site, ordered by name. Administrators only."""
    list_dto = ListSitesInputDTO(actor=actor)
    return await use_case.execute(list_dto)


@router.put(
    "/{id_site}",
    response_model=SiteOutputDTO,
    summary="Update a site",
)
async def update_site(
    request: UpdateSiteRequest,
    id_site: int = Path(..., ge=1),
    actor: ActorDTO = Depends(require_admin),
    use_case=Depends(get_update_site_use_case),
) -> SiteOutputDTO:
    """Update the name and/or address of an existing site."""
    update_dto = UpdateSiteInputDTO(
        actor=actor,
        id_site=id_site,
        name=request.name,
        address=request.address,
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
    actor: ActorDTO = Depends(require_admin),
    use_case=Depends(get_deactivate_site_use_case),
) -> None:
    """Deactivate a site. Rejected when clients are associated with it."""
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
