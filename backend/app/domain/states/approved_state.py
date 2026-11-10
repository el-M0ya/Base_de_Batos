"""Terminal state of an approved routine."""

from __future__ import annotations

from app.domain.entities.routine import RoutineStatus
from app.domain.states.routine_state import RoutineState


class ApprovedState(RoutineState):
    """An approved routine cannot transition to another lifecycle state."""

    status = RoutineStatus.APPROVED
    allowed_transitions = frozenset()
