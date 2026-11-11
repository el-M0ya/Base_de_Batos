"""Base State object for the ``Routine`` lifecycle.

Each concrete state owns its outgoing transitions. ``Routine`` delegates the
lifecycle methods to the state derived from its persisted status, so adding a
new transition only requires changing the relevant state class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from app.domain.entities.routine import RoutineStatus
from app.domain.exceptions.domain_exceptions import (
    InvalidRoutineStateTransition,
    RejectedValidationRequiresObservations,
)

if TYPE_CHECKING:
    from app.domain.entities.routine import Routine


class RoutineState(ABC):
    """Base class for the states of a routine."""

    @property
    @abstractmethod
    def status(self) -> RoutineStatus:
        """Persisted status represented by this state."""

    allowed_transitions: ClassVar[frozenset[RoutineStatus]] = frozenset()

    def can_transition_to(self, target: RoutineStatus) -> bool:
        return target in self.allowed_transitions

    def submit_for_review(self, routine: Routine) -> None:
        self._transition_to(routine, RoutineStatus.PENDING_REVIEW)

    def approve(self, routine: Routine) -> None:
        self._transition_to(routine, RoutineStatus.APPROVED)

    def reject(self, routine: Routine, observations: str | None = None) -> None:
        if RoutineStatus.REJECTED not in self.allowed_transitions:
            raise InvalidRoutineStateTransition(
                self.status, RoutineStatus.REJECTED
            )
        if not isinstance(observations, str) or not observations.strip():
            raise RejectedValidationRequiresObservations()
        routine._set_status(RoutineStatus.REJECTED)

    def replace(self, routine: Routine) -> None:
        self._transition_to(routine, RoutineStatus.REPLACED)

    def _transition_to(
        self, routine: Routine, target: RoutineStatus
    ) -> None:
        if target not in self.allowed_transitions:
            raise InvalidRoutineStateTransition(self.status, target)
        routine._set_status(target)


class DraftState(RoutineState):
    """A routine being authored; it can be submitted for review."""

    status = RoutineStatus.DRAFT
    allowed_transitions = frozenset({RoutineStatus.PENDING_REVIEW})
