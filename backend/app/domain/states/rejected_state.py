"""State of a routine rejected during review."""

from __future__ import annotations

from app.domain.entities.routine import RoutineStatus
from app.domain.states.routine_state import RoutineState


class RejectedState(RoutineState):
    """A rejected routine can be corrected and resubmitted for review."""

    status = RoutineStatus.REJECTED
    allowed_transitions = frozenset({RoutineStatus.PENDING_REVIEW})
