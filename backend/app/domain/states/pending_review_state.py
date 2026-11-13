"""State of a routine waiting for review."""

from __future__ import annotations

from app.domain.entities.routine import RoutineStatus
from app.domain.states.routine_state import RoutineState


class PendingReviewState(RoutineState):
    """The routine can be approved, rejected or replaced."""

    status = RoutineStatus.PENDING_REVIEW
    allowed_transitions = frozenset(
        {
            RoutineStatus.APPROVED,
            RoutineStatus.REJECTED,
            RoutineStatus.REPLACED,
        }
    )
