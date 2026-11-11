"""Terminal state of a routine replaced by a newer routine."""

from __future__ import annotations

from app.domain.entities.routine import RoutineStatus
from app.domain.states.routine_state import RoutineState


class ReplacedState(RoutineState):
    """A replaced routine is kept for lineage and cannot be edited again."""

    status = RoutineStatus.REPLACED
    allowed_transitions = frozenset()
