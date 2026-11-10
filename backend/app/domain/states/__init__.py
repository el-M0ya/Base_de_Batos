"""State objects and persisted-status conversion for the ``Routine`` lifecycle.

``REPLACED`` belongs to the domain lifecycle but is not yet accepted by the
``chk_routine_status`` constraint in the physical schema. The mapping below is
ready for the migration that adds it; until then, replacement lineage is only
enforced in the domain."""

from __future__ import annotations

from app.domain.entities.routine import RoutineStatus
from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.states.approved_state import ApprovedState
from app.domain.states.pending_review_state import PendingReviewState
from app.domain.states.rejected_state import RejectedState
from app.domain.states.replaced_state import ReplacedState
from app.domain.states.routine_state import DraftState, RoutineState

_STATE_BY_STATUS: dict[RoutineStatus, type[RoutineState]] = {
    RoutineStatus.DRAFT: DraftState,
    RoutineStatus.PENDING_REVIEW: PendingReviewState,
    RoutineStatus.APPROVED: ApprovedState,
    RoutineStatus.REJECTED: RejectedState,
    RoutineStatus.REPLACED: ReplacedState,
}


def state_for_status(value: object) -> RoutineState:
    """Return a new state object for an enum member or persisted string."""
    if isinstance(value, RoutineState):
        return value
    if isinstance(value, RoutineStatus):
        status = value
    elif isinstance(value, str):
        try:
            status = RoutineStatus(value.strip().upper())
        except ValueError as exc:
            raise InvalidDomainValue(
                "status",
                value,
                f"one of {[item.value for item in RoutineStatus]}",
            ) from exc
    else:
        raise InvalidDomainValue(
            "status",
            value,
            f"one of {[item.value for item in RoutineStatus]}",
        )

    return _STATE_BY_STATUS[status]()


def state_from_persisted(value: object) -> RoutineState:
    """Explicit alias used by persistence adapters."""
    return state_for_status(value)


def status_for_state(state: RoutineState) -> RoutineStatus:
    """Return the persisted status represented by ``state``."""
    if not isinstance(state, RoutineState):
        raise InvalidDomainValue(
            "state", state, "a RoutineState instance"
        )
    return state.status


def persisted_value_for_state(state: RoutineState) -> str:
    """Return the value to store when persisting ``state``."""
    return status_for_state(state).value


__all__ = [
    "ApprovedState",
    "DraftState",
    "PendingReviewState",
    "RejectedState",
    "ReplacedState",
    "RoutineState",
    "persisted_value_for_state",
    "state_for_status",
    "state_from_persisted",
    "status_for_state",
]
