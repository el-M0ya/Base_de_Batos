"""Exercise catalog HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.adapters.presentation.api.dependencies import (
    get_current_actor,
    get_exercise_dependencies,
)
from app.adapters.presentation.api.schemas.exercise_schema import CatalogResponse
from app.application.dto.actor import ActorDTO
from app.infrastructure.dependencies import ExerciseDependencies

router = APIRouter(prefix="/catalogs", tags=["Catalogs"])


@router.get("/exercises", response_model=CatalogResponse)
async def list_exercise_catalogs(
    actor: ActorDTO = Depends(get_current_actor),
    dependencies: ExerciseDependencies = Depends(get_exercise_dependencies),
) -> CatalogResponse:
    result = await dependencies.list_catalogs.execute(actor)
    return CatalogResponse.from_dto(result)
