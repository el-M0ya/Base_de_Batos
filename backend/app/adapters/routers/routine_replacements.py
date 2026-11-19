"""Endpoint for requesting a successor to a reviewed routine."""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.dependencies import get_current_actor, get_replace_routine_use_case
from app.adapters.routers._errors import to_http_exception
from app.application.dto.actor import ActorDTO
from app.application.dto.routine_replacement_dto import ReplaceRoutineInputDTO
from app.application.exceptions import ApplicationError, InvalidInput
from app.application.use_cases.replace_routine import ReplaceRoutineUseCase
from app.domain.entities.routine import RoutineStatus
from app.domain.exceptions.domain_exceptions import DomainException

router = APIRouter(prefix="/routines", tags=["routines"])


class ReplaceRoutineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy_name: str = Field(default="balanced", min_length=1, max_length=100)
    total_exercises: int = Field(gt=0)
    target_intensity: str = Field(min_length=1, max_length=50)
    exercise_type_proportions: dict[str, Decimal]
    request_date: date = Field(default_factory=date.today)


class RoutineReplacementResponse(BaseModel):
    id_replaced_routine: int
    replaced_status: RoutineStatus
    id_successor_routine: int
    id_routine_origin: int
    id_workout_program: int
    id_trainer_creator: int
    successor_status: RoutineStatus
    creation_date: date


@router.post(
    "/{id_routine}/replacement",
    response_model=RoutineReplacementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a successor for a reviewed routine",
)
async def replace_routine(
    request: ReplaceRoutineRequest,
    id_routine: int = Path(ge=1),
    actor: ActorDTO = Depends(get_current_actor),
    use_case: ReplaceRoutineUseCase = Depends(get_replace_routine_use_case),
) -> RoutineReplacementResponse:
    try:
        result = await use_case.execute(
            ReplaceRoutineInputDTO(
                actor=actor,
                id_routine=id_routine,
                strategy_name=request.strategy_name,
                total_exercises=request.total_exercises,
                target_intensity=request.target_intensity,
                exercise_type_proportions=request.exercise_type_proportions,
                request_date=request.request_date,
            )
        )
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error

    source = result.replaced_routine
    successor = result.generated_successor.routine
    if source.id_routine is None or successor.id_routine is None:
        raise to_http_exception(
            InvalidInput("The replacement did not return persisted routine IDs.")
        )
    return RoutineReplacementResponse(
        id_replaced_routine=source.id_routine,
        replaced_status=source.status,
        id_successor_routine=successor.id_routine,
        id_routine_origin=successor.id_routine_origin or source.id_routine,
        id_workout_program=successor.id_workout_program,
        id_trainer_creator=successor.id_trainer_creator,
        successor_status=successor.status,
        creation_date=successor.creation_date,
    )
