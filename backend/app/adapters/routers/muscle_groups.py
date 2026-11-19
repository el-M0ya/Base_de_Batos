"""FastAPI router for muscle group catalog management (U-3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.dependencies import (
    _admin_actor,
    get_create_muscle_group_use_case,
    get_delete_muscle_group_use_case,
    get_get_muscle_group_use_case,
    get_list_muscle_groups_use_case,
    get_update_muscle_group_use_case,
)
from app.adapters.routers._errors import to_http_exception
from app.application.dto.muscle_group_dto import (
    CreateMuscleGroupInputDTO,
    DeleteMuscleGroupInputDTO,
    MuscleGroupOutputDTO,
    UpdateMuscleGroupInputDTO,
)
from app.application.exceptions import ApplicationError
from app.domain.exceptions.domain_exceptions import DomainException

router = APIRouter(prefix="/muscle-groups", tags=["muscle groups"])


class MuscleGroupRequest(BaseModel):
    """Fields accepted when creating or renaming a muscle group."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)


@router.get(
    "",
    response_model=list[MuscleGroupOutputDTO],
    summary="List muscle groups",
)
async def list_muscle_groups(
    use_case=Depends(get_list_muscle_groups_use_case),
) -> list[MuscleGroupOutputDTO]:
    """Return every muscle group ordered by name."""
    return await use_case.execute()


@router.post(
    "",
    response_model=MuscleGroupOutputDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a muscle group",
)
async def create_muscle_group(
    body: MuscleGroupRequest,
    use_case=Depends(get_create_muscle_group_use_case),
) -> MuscleGroupOutputDTO:
    """Register a new muscle group. Only administrators may create them."""
    try:
        input_dto = CreateMuscleGroupInputDTO(
            actor=_admin_actor(),
            name=body.name,
        )
        return await use_case.execute(input_dto)
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error


@router.get(
    "/{id_muscle_group}",
    response_model=MuscleGroupOutputDTO,
    summary="Get a muscle group by identifier",
)
async def get_muscle_group(
    id_muscle_group: int = Path(..., ge=1),
    use_case=Depends(get_get_muscle_group_use_case),
) -> MuscleGroupOutputDTO:
    """Return the muscle group with the given identifier."""
    try:
        return await use_case.execute(id_muscle_group)
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error


@router.put(
    "/{id_muscle_group}",
    response_model=MuscleGroupOutputDTO,
    summary="Rename a muscle group",
)
async def update_muscle_group(
    body: MuscleGroupRequest,
    id_muscle_group: int = Path(..., ge=1),
    use_case=Depends(get_update_muscle_group_use_case),
) -> MuscleGroupOutputDTO:
    """Update the name of an existing muscle group."""
    try:
        input_dto = UpdateMuscleGroupInputDTO(
            actor=_admin_actor(),
            id_muscle_group=id_muscle_group,
            name=body.name,
        )
        return await use_case.execute(input_dto)
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error


@router.delete(
    "/{id_muscle_group}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a muscle group",
)
async def delete_muscle_group(
    id_muscle_group: int = Path(..., ge=1),
    use_case=Depends(get_delete_muscle_group_use_case),
) -> None:
    """Delete a muscle group when no exercise or program references it."""
    try:
        input_dto = DeleteMuscleGroupInputDTO(
            actor=_admin_actor(),
            id_muscle_group=id_muscle_group,
        )
        await use_case.execute(input_dto)
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error
