"""FastAPI routes for routine generation and retrieval (issue E6-03).

Exposes:

* ``POST /routines`` — accepts generation parameters and returns the created
  routine with identifier, program, creator, date, status, parameters and
  composition.
* ``GET /routines/{id_routine}`` — returns a complete routine by identifier,
  including its nested JSONB structure.

All endpoints are protected with authentication (``get_current_actor``) and
program-level authorization enforced by the application use cases. Domain and
application errors are translated to the uniform API error format through
``to_http_exception``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.dependencies import (
    get_current_actor,
    get_generate_routine_use_case,
    get_get_routine_use_case,
)
from app.adapters.routers._errors import to_http_exception
from app.application.dto.actor import ActorDTO
from app.application.dto.routine_generation_dto import (
    GenerateRoutineInputDTO,
    GeneratedRoutineOutputDTO,
)
from app.application.dto.routine_retrieval_dto import GetRoutineInputDTO
from app.application.exceptions import ApplicationError
from app.application.use_cases.generate_routine import GenerateRoutineUseCase
from app.application.use_cases.get_routine import GetRoutineUseCase
from app.domain.exceptions.domain_exceptions import DomainException

router = APIRouter(prefix="/routines", tags=["routines"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class CompositionEntry(BaseModel):
    """One exercised item inside a routine's composition."""

    model_config = ConfigDict(extra="forbid")

    id_exercise: int
    execution_order: int
    sets: int
    repetitions: int
    rest_seconds: int


class ParametersResponse(BaseModel):
    """Generation-parameter snapshot attached to a routine."""

    model_config = ConfigDict(extra="forbid")

    total_exercises: int
    intensity_level: str
    cardio_ratio: str
    strength_ratio: str
    flexibility_ratio: str
    covered_muscle_group_ids: list[int]


class RoutineResponse(BaseModel):
    """Complete routine exposed through the API."""

    model_config = ConfigDict(extra="forbid")

    id_routine: int
    id_workout_program: int
    id_trainer_creator: int
    creation_date: date
    status: str
    parameters: ParametersResponse
    composition: list[CompositionEntry]
    structure: dict


class GenerateRoutineRequest(BaseModel):
    """Parameters to request automatic routine generation."""

    model_config = ConfigDict(extra="forbid")

    id_workout_program: int = Field(ge=1)
    strategy_name: str = Field(default="balanced", min_length=1, max_length=100)
    total_exercises: int = Field(gt=0)
    target_intensity: str = Field(min_length=1, max_length=50)
    exercise_type_proportions: dict[str, Decimal]
    generation_date: date = Field(default_factory=date.today)
    id_routine_origin: int | None = Field(default=None, ge=1)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

def _map_output_to_response(output: GeneratedRoutineOutputDTO) -> RoutineResponse:
    """Map a generation/retrieval output DTO to the public response model.

    Shared by both endpoints so generation and retrieval expose the exact same
    response shape (DRY).
    """
    routine = output.routine
    parameters = output.parameters

    composition: list[CompositionEntry] = []
    for entry in output.composition:
        if isinstance(entry, dict):
            composition.append(
                CompositionEntry(
                    id_exercise=entry["id_exercise"],
                    execution_order=entry["execution_order"],
                    sets=entry["sets"],
                    repetitions=entry["repetitions"],
                    rest_seconds=entry["rest_seconds"],
                )
            )
        else:
            # GeneratedExercise coming from the generation use case.
            composition.append(
                CompositionEntry(
                    id_exercise=entry.exercise.id_exercise,
                    execution_order=entry.order,
                    sets=entry.sets,
                    repetitions=entry.repetitions,
                    rest_seconds=entry.rest_seconds,
                )
            )

    return RoutineResponse(
        id_routine=routine.id_routine,
        id_workout_program=routine.id_workout_program,
        id_trainer_creator=routine.id_trainer_creator,
        creation_date=routine.creation_date,
        status=routine.status.value,
        parameters=ParametersResponse(
            total_exercises=parameters.total_exercises,
            intensity_level=parameters.intensity_level.value,
            cardio_ratio=str(parameters.cardio_ratio),
            strength_ratio=str(parameters.strength_ratio),
            flexibility_ratio=str(parameters.flexibility_ratio),
            covered_muscle_group_ids=parameters.covered_muscle_group_ids,
        ),
        composition=composition,
        structure=output.structure.to_dict(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=RoutineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a training routine automatically",
)
async def generate_routine(
    request: GenerateRoutineRequest,
    actor: ActorDTO = Depends(get_current_actor),
    use_case: GenerateRoutineUseCase = Depends(get_generate_routine_use_case),
) -> RoutineResponse:
    """Generate and persist a routine for the requested program.

    The authenticated trainer must hold an effective ``can_generate``
    authorisation for the program. Invalid parameters are rejected before the
    strategy is invoked, so no row is written for a bad request.
    """
    try:
        result = await use_case.execute(
            GenerateRoutineInputDTO(
                actor=actor,
                id_workout_program=request.id_workout_program,
                strategy_name=request.strategy_name,
                total_exercises=request.total_exercises,
                target_intensity=request.target_intensity,
                exercise_type_proportions=request.exercise_type_proportions,
                generation_date=request.generation_date,
                id_routine_origin=request.id_routine_origin,
            )
        )
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error

    return _map_output_to_response(result)


@router.get(
    "/{id_routine}",
    response_model=RoutineResponse,
    summary="Retrieve a complete routine by identifier",
)
async def get_routine(
    id_routine: int = Path(ge=1),
    actor: ActorDTO = Depends(get_current_actor),
    use_case: GetRoutineUseCase = Depends(get_get_routine_use_case),
) -> RoutineResponse:
    """Return the complete routine including its nested JSONB structure.

    The authenticated trainer must hold an effective ``can_generate``
    authorisation for the routine's program. The JSONB structure is returned
    deserialized, without information loss.
    """
    try:
        result = await use_case.execute(
            GetRoutineInputDTO(actor=actor, id_routine=id_routine)
        )
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error

    return _map_output_to_response(result)
