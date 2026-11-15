"""FastAPI router for training program and coverage management (RF-10)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.dependencies import (
    _admin_actor,
    get_create_training_program_use_case,
    get_delete_training_program_use_case,
    get_get_training_program_use_case,
    get_list_training_programs_use_case,
    get_set_training_program_muscle_groups_use_case,
    get_update_training_program_use_case,
)
from app.adapters.routers._errors import to_http_exception
from app.application.dto.muscle_group_dto import MuscleGroupOutputDTO
from app.application.dto.training_program_dto import (
    CreateTrainingProgramInputDTO,
    DeleteTrainingProgramInputDTO,
    SetTrainingProgramMuscleGroupsInputDTO,
    TrainingProgramOutputDTO,
    UpdateTrainingProgramInputDTO,
)
from app.application.exceptions import ApplicationError
from app.domain.exceptions.domain_exceptions import DomainException

router = APIRouter(prefix="/training-programs", tags=["training programs"])


class TrainingProgramRequest(BaseModel):
    """Fields accepted when creating or updating a training program."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    objective: str = Field(min_length=1)
    muscle_group_ids: list[int] = Field(default_factory=list)


class ProgramCoverageRequest(BaseModel):
    """Muscle groups that a training program must cover."""

    model_config = ConfigDict(extra="forbid")

    muscle_group_ids: list[int] = Field(default_factory=list)


@router.get(
    "",
    response_model=list[TrainingProgramOutputDTO],
    summary="List training programs",
)
async def list_training_programs(
    use_case=Depends(get_list_training_programs_use_case),
) -> list[TrainingProgramOutputDTO]:
    """Return every training program with its covered muscle groups."""
    return await use_case.execute()


@router.post(
    "",
    response_model=TrainingProgramOutputDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a training program",
)
async def create_training_program(
    body: TrainingProgramRequest,
    use_case=Depends(get_create_training_program_use_case),
) -> TrainingProgramOutputDTO:
    """Register a program and assign the muscle groups it must cover."""
    try:
        input_dto = CreateTrainingProgramInputDTO(
            actor=_admin_actor(),
            name=body.name,
            objective=body.objective,
            muscle_group_ids=tuple(body.muscle_group_ids),
        )
        return await use_case.execute(input_dto)
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error


@router.get(
    "/{id_workout_program}",
    response_model=TrainingProgramOutputDTO,
    summary="Get a training program by identifier",
)
async def get_training_program(
    id_workout_program: int = Path(..., ge=1),
    use_case=Depends(get_get_training_program_use_case),
) -> TrainingProgramOutputDTO:
    """Return a program and its covered muscle groups."""
    try:
        return await use_case.execute(id_workout_program)
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error


@router.put(
    "/{id_workout_program}",
    response_model=TrainingProgramOutputDTO,
    summary="Update a training program",
)
async def update_training_program(
    body: TrainingProgramRequest,
    id_workout_program: int = Path(..., ge=1),
    use_case=Depends(get_update_training_program_use_case),
) -> TrainingProgramOutputDTO:
    """Update a program and replace its covered muscle groups."""
    try:
        input_dto = UpdateTrainingProgramInputDTO(
            actor=_admin_actor(),
            id_workout_program=id_workout_program,
            name=body.name,
            objective=body.objective,
            muscle_group_ids=tuple(body.muscle_group_ids),
        )
        return await use_case.execute(input_dto)
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error


@router.delete(
    "/{id_workout_program}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a training program",
)
async def delete_training_program(
    id_workout_program: int = Path(..., ge=1),
    use_case=Depends(get_delete_training_program_use_case),
) -> None:
    """Delete a program and its coverage when no other relation references it."""
    try:
        input_dto = DeleteTrainingProgramInputDTO(
            actor=_admin_actor(),
            id_workout_program=id_workout_program,
        )
        await use_case.execute(input_dto)
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error


@router.get(
    "/{id_workout_program}/muscle-groups",
    response_model=list[MuscleGroupOutputDTO],
    summary="Get the muscle groups covered by a program",
)
async def get_program_coverage(
    id_workout_program: int = Path(..., ge=1),
    use_case=Depends(get_get_training_program_use_case),
) -> list[MuscleGroupOutputDTO]:
    """Return the muscle groups associated with a program."""
    try:
        program = await use_case.execute(id_workout_program)
        return list(program.muscle_groups)
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error


@router.put(
    "/{id_workout_program}/muscle-groups",
    response_model=TrainingProgramOutputDTO,
    summary="Replace the muscle groups covered by a program",
)
async def set_program_coverage(
    body: ProgramCoverageRequest,
    id_workout_program: int = Path(..., ge=1),
    use_case=Depends(get_set_training_program_muscle_groups_use_case),
) -> TrainingProgramOutputDTO:
    """Replace the coverage of a program atomically."""
    try:
        input_dto = SetTrainingProgramMuscleGroupsInputDTO(
            actor=_admin_actor(),
            id_workout_program=id_workout_program,
            muscle_group_ids=tuple(body.muscle_group_ids),
        )
        return await use_case.execute(input_dto)
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error
