"""FastAPI routes for program-scoped routine consultation (RF-19).

Allows a trainer to consult routines created by other trainers who serve the
same authorized training program. SQL stays in the repository layer; the route
only orchestrates the use case.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.adapters.dependencies import (
    get_current_actor,
    get_list_routines_for_trainer_use_case,
)
from app.application.dto.actor import ActorDTO
from app.application.dto.routine_dto import (
    ListRoutinesForTrainerInputDTO,
    RoutineSummaryDTO,
)
from app.application.exceptions import ApplicationError, PermissionDenied

router = APIRouter(prefix="/training-programs", tags=["routine consultation"])


@router.get(
    "/{id_workout_program}/routines",
    response_model=tuple[RoutineSummaryDTO, ...],
    summary="List routines from other trainers in the same authorized program",
)
async def list_routines_for_trainer(
    id_workout_program: int = Path(..., ge=1),
    actor: ActorDTO = Depends(get_current_actor),
    use_case=Depends(get_list_routines_for_trainer_use_case),
) -> tuple[RoutineSummaryDTO, ...]:
    """Return routines visible to the authenticated trainer in a program.

    Only routines created by *other* trainers who are authorized for the same
    program are exposed. Routines from unrelated programs are never returned.
    """
    try:
        input_dto = ListRoutinesForTrainerInputDTO(
            actor=actor,
            id_workout_program=id_workout_program,
        )
        return await use_case.execute(input_dto)
    except PermissionDenied as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error
    except ApplicationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
