"""Exercise HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.adapters.presentation.api.dependencies import (
    get_current_actor,
    get_exercise_dependencies,
)
from app.adapters.presentation.api.schemas.exercise_schema import (
    CreateExerciseRequest,
    ExerciseResponse,
)
from app.application.dto.actor import ActorDTO
from app.application.dto.exercise_dto import (
    CreateExerciseInputDTO,
    ListExercisesInputDTO,
)
from app.infrastructure.dependencies import ExerciseDependencies

router = APIRouter(prefix="/exercises", tags=["Exercises"])


@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    payload: CreateExerciseRequest,
    actor: ActorDTO = Depends(get_current_actor),
    dependencies: ExerciseDependencies = Depends(get_exercise_dependencies),
) -> ExerciseResponse:
    result = await dependencies.create_exercise.execute(
        CreateExerciseInputDTO(
            actor=actor,
            name=payload.name,
            exercise_type=payload.exercise_type,
            intensity=payload.intensity,
            muscle_group_id=payload.muscle_group_id,
            description=payload.description,
            registration_date=payload.registration_date,
        )
    )
    return ExerciseResponse.from_dto(result)


@router.get("", response_model=list[ExerciseResponse])
async def list_exercises(
    muscle_group_id: int | None = Query(default=None, gt=0),
    exercise_type: str | None = None,
    intensity: str | None = None,
    order_by: str = "name",
    descending: bool = False,
    actor: ActorDTO = Depends(get_current_actor),
    dependencies: ExerciseDependencies = Depends(get_exercise_dependencies),
) -> list[ExerciseResponse]:
    result = await dependencies.list_exercises.execute(
        ListExercisesInputDTO(
            actor=actor,
            muscle_group_id=muscle_group_id,
            exercise_type=exercise_type,
            intensity=intensity,
            order_by=order_by,
            descending=descending,
        )
    )
    return [ExerciseResponse.from_dto(item) for item in result]
