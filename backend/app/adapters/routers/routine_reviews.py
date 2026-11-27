"""FastAPI routes for routine review and validation (issue E6-04).

Exposes:

* ``GET /routines/pending-review`` — retrieves routines pending review that the
  authenticated trainer is authorised to validate.
* ``POST /routines/{id_routine}/review`` — registers an approval or rejection
  decision for a routine.

All endpoints are protected with authentication (``get_current_actor``) and
enforce ``can_validate`` program-level authorisation in the application use
cases. Domain and application errors are translated to the uniform API error
format through ``to_http_exception``. No business rules are placed in the
controller; all decisions are delegated to the application use cases.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.dependencies import (
    get_current_actor,
    get_list_pending_reviews_use_case,
    get_review_routine_use_case,
)
from app.adapters.routers._errors import to_http_exception
from app.application.dto.actor import ActorDTO
from app.application.dto.routine_dto import RoutineSummaryDTO
from app.application.dto.routine_review_dto import (
    ListPendingReviewsInputDTO,
    ReviewRoutineInputDTO,
    RoutineValidationOutputDTO,
)
from app.application.exceptions import ApplicationError
from app.application.use_cases.list_pending_reviews import ListPendingReviewsUseCase
from app.application.use_cases.review_routine import ReviewRoutineUseCase
from app.domain.entities.routine import RoutineStatus
from app.domain.entities.routine_validation import ValidationDecision
from app.domain.exceptions.domain_exceptions import DomainException

router = APIRouter(prefix="/routines", tags=["routine reviews"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class ReviewRequest(BaseModel):
    """Decision to approve or reject a routine under review."""

    model_config = ConfigDict(extra="forbid")

    decision: str = Field(
        min_length=1,
        max_length=20,
        description="APPROVED or REJECTED",
    )
    observations: Optional[str] = Field(
        default=None,
        description="Required when decision is REJECTED.",
    )
    validation_date: Optional[date] = Field(
        default=None,
        description="Defaults to today.",
    )


class ReviewResponse(BaseModel):
    """Outcome of a routine review decision."""

    model_config = ConfigDict(extra="forbid")

    id_validation: int
    id_routine: int
    id_room_chief: int
    decision: str
    validation_date: date
    observations: Optional[str]
    routine_status: Optional[str]


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

def _map_validation_to_response(dto: RoutineValidationOutputDTO) -> ReviewResponse:
    """Map a validation output DTO to the public response model."""
    return ReviewResponse(
        id_validation=dto.id_validation,
        id_routine=dto.id_routine,
        id_room_chief=dto.id_room_chief,
        decision=dto.decision.value,
        validation_date=dto.validation_date,
        observations=dto.observations,
        routine_status=dto.routine_status.value if dto.routine_status else None,
    )


def _parse_decision(value: str) -> ValidationDecision:
    """Parse a decision string into a ValidationDecision, raising on invalid."""
    try:
        return ValidationDecision(value)
    except ValueError as error:
        raise DomainException(
            f"invalid decision {value!r}; one of "
            f"{[d.value for d in ValidationDecision]}"
        ) from error


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/pending-review",
    response_model=tuple[RoutineSummaryDTO, ...],
    summary="List routines pending review for an authorised reviewer",
)
async def list_pending_reviews(
    actor: ActorDTO = Depends(get_current_actor),
    use_case: ListPendingReviewsUseCase = Depends(get_list_pending_reviews_use_case),
) -> tuple[RoutineSummaryDTO, ...]:
    """Return routines in PENDING_REVIEW the actor may validate.

    Only routines from programs where the actor holds an effective
    ``can_validate`` authorisation are exposed.
    """
    try:
        return await use_case.execute(
            ListPendingReviewsInputDTO(actor=actor)
        )
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error


@router.post(
    "/{id_routine}/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Register an approval or rejection decision for a routine",
)
async def review_routine(
    request: ReviewRequest,
    id_routine: int = Path(ge=1),
    actor: ActorDTO = Depends(get_current_actor),
    use_case: ReviewRoutineUseCase = Depends(get_review_routine_use_case),
) -> ReviewResponse:
    """Record an approval or rejection decision for a pending routine.

    The authenticated trainer must hold an effective ``can_validate``
    authorisation for the routine's program. A rejection requires non-empty
    observations. Invalid state transitions and missing observations are
    rejected with standard API errors.
    """
    try:
        result = await use_case.execute(
            ReviewRoutineInputDTO(
                actor=actor,
                id_routine=id_routine,
                decision=_parse_decision(request.decision),
                observations=request.observations,
                validation_date=request.validation_date or date.today(),
            )
        )
    except (ApplicationError, DomainException) as error:
        raise to_http_exception(error) from error

    return _map_validation_to_response(result)
