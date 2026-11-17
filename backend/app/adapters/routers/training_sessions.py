"""Client endpoints to record and consult completed training sessions."""

from __future__ import annotations

from datetime import date, time

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.dependencies import (
    get_current_actor,
    get_list_training_sessions_use_case,
    get_register_training_session_use_case,
)
from app.adapters.routers._errors import to_http_exception
from app.application.dto.actor import ActorDTO
from app.application.dto.training_session_dto import (
    RegisterTrainingSessionInputDTO,
    TrainingSessionOutputDTO,
)
from app.application.exceptions import ApplicationError
from app.application.use_cases.list_training_sessions import (
    ListTrainingSessionsUseCase,
)
from app.application.use_cases.register_training_session import (
    RegisterTrainingSessionUseCase,
)
from app.domain.exceptions.domain_exceptions import DomainException

router = APIRouter(prefix="/assignments", tags=["training sessions"])


class RegisterTrainingSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_date: date
    start_time: time
    end_time: time
    intensity_perceived: int = Field(ge=1, le=10)
    completed: bool
    observations: str | None = Field(default=None, max_length=5000)


@router.post(
    "/{id_assignment}/sessions",
    response_model=TrainingSessionOutputDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Register a training session",
)
async def register_training_session(
    request: RegisterTrainingSessionRequest,
    id_assignment: int = Path(ge=1),
    actor: ActorDTO = Depends(get_current_actor),
    use_case: RegisterTrainingSessionUseCase = Depends(
        get_register_training_session_use_case
    ),
) -> TrainingSessionOutputDTO:
    try:
        return await use_case.execute(
            RegisterTrainingSessionInputDTO(
                actor=actor,
                id_assignment=id_assignment,
                session_date=request.session_date,
                start_time=request.start_time,
                end_time=request.end_time,
                intensity_perceived=request.intensity_perceived,
                completed=request.completed,
                observations=request.observations,
            )
        )
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error


@router.get(
    "/{id_assignment}/sessions",
    response_model=list[TrainingSessionOutputDTO],
    summary="List a client's training sessions",
)
async def list_training_sessions(
    id_assignment: int = Path(ge=1),
    actor: ActorDTO = Depends(get_current_actor),
    use_case: ListTrainingSessionsUseCase = Depends(
        get_list_training_sessions_use_case
    ),
) -> list[TrainingSessionOutputDTO]:
    try:
        return list(await use_case.execute(actor, id_assignment))
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error
