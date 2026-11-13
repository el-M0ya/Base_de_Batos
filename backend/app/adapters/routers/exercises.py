"""HTTP endpoints for the exercise bank.

Only the reclassification operation belongs to issue E5-01. The endpoint is
mounted under ``/api/v1`` by the application factory.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.dependencies import get_actor, get_reclassify_exercise_use_case
from app.adapters.routers._errors import to_http_exception
from app.application.dto.actor import ActorDTO
from app.application.dto.exercise_dto import (
    ExerciseOutputDTO,
    ReclassifyExerciseInputDTO,
)
from app.application.exceptions import ApplicationError
from app.application.use_cases.reclassify_exercise import ReclassifyExerciseUseCase
from app.domain.exceptions.domain_exceptions import DomainException

router = APIRouter(prefix="/exercises", tags=["exercises"])


class ReclassifyExerciseRequest(BaseModel):
    """Body accepted by the reclassification endpoint."""

    model_config = ConfigDict(extra="forbid")

    exercise_type: str = Field(min_length=1, max_length=50)
    intensity: str = Field(min_length=1, max_length=50)
    muscle_group_id: int = Field(ge=1)


@router.put(
    "/{id_exercise}/classification",
    response_model=ExerciseOutputDTO,
    status_code=status.HTTP_200_OK,
    summary="Reclassify an exercise",
    description=(
        "Changes the exercise type, intensity and muscle group of an exercise. "
        "Only the trainer that created the exercise can perform this operation."
    ),
)
async def reclassify_exercise(
    body: ReclassifyExerciseRequest,
    id_exercise: int = Path(ge=1),
    actor: ActorDTO = Depends(get_actor),
    use_case: ReclassifyExerciseUseCase = Depends(get_reclassify_exercise_use_case),
) -> ExerciseOutputDTO:
    """Reclassify an exercise, translating application errors to HTTP errors."""
    try:
        return await use_case.execute(
            ReclassifyExerciseInputDTO(
                actor=actor,
                id_exercise=id_exercise,
                exercise_type=body.exercise_type,
                intensity=body.intensity,
                muscle_group_id=body.muscle_group_id,
            )
        )
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error
