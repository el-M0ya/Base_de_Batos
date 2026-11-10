"""Domain Entitie ``Routine`` """

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidRoutineReference,
)

if TYPE_CHECKING:
    from app.domain.states import RoutineState


class RoutineStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    # Domain state that still requires a migration of chk_routine_status.
    REPLACED = "REPLACED"


def _ensure_positive_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


def _ensure_date(value: object, field_name: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise InvalidDomainValue(field_name, value, "a date")


@dataclass
class Routine:
    id_workout_program: int
    id_trainer_creator: int
    id_routine: Optional[int] = None
    status: RoutineStatus = RoutineStatus.DRAFT
    creation_date: date = field(default_factory=date.today)
    id_client: Optional[int] = None
    id_routine_origin: Optional[int] = None

    def __post_init__(self) -> None:
        self.validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_status(value: object) -> RoutineStatus:
        if isinstance(value, RoutineStatus):
            return value
        try:
            return RoutineStatus(value)  # type: ignore[arg-type]
        except ValueError as exc:
            raise InvalidDomainValue(
                "status", value, f"one of {[s.value for s in RoutineStatus]}"
            ) from exc

    def _validate_fields(self) -> None:
        self.status = self._coerce_status(self.status)
        _ensure_positive_int(self.id_workout_program, "id_workout_program")
        _ensure_positive_int(self.id_trainer_creator, "id_trainer_creator")
        _ensure_date(self.creation_date, "creation_date")

        if self.id_routine is not None:
            _ensure_positive_int(self.id_routine, "id_routine")

        if self.id_client is not None:
            _ensure_positive_int(self.id_client, "id_client")

        if self.id_routine_origin is not None:
            _ensure_positive_int(self.id_routine_origin, "id_routine_origin")
            self._ensure_origin_is_not_self()

    def _ensure_origin_is_not_self(self) -> None:
        if self.id_routine is not None and self.id_routine_origin == self.id_routine:
            raise InvalidRoutineReference(self.id_routine, self.id_routine_origin)

    def validate(self) -> None:
        self._validate_fields()

    # ------------------------------------------------------------------
    # Life cycle (delegated to the current State object)
    # ------------------------------------------------------------------
    @property
    def state(self) -> "RoutineState":
        """Return the State object that represents the persisted status."""
        from app.domain.states import state_for_status

        return state_for_status(self.status)

    def _set_status(self, target: RoutineStatus) -> None:
        """Apply a transition already authorised by the current State."""
        self.status = self._coerce_status(target)

    def can_transition_to(self, target: RoutineStatus) -> bool:
        return self.state.can_transition_to(self._coerce_status(target))

    def submit_for_review(self) -> None:
        self.state.submit_for_review(self)

    def resubmit_for_review(self) -> None:
        self.state.submit_for_review(self)

    def approve(self) -> None:
        self.state.approve(self)

    def reject(self, observations: str | None = None) -> None:
        self.state.reject(self, observations)

    def replace(self) -> None:
        self.state.replace(self)

    # ------------------------------------------------------------------
    # Procedence
    # ------------------------------------------------------------------
    def set_origin(self, origin_id: int) -> None:
        _ensure_positive_int(origin_id, "id_routine_origin")
        self.id_routine_origin = origin_id
        self._ensure_origin_is_not_self()

    def clear_origin(self) -> None:
        self.id_routine_origin = None

    # ------------------------------------------------------------------
    # State Consult
    # ------------------------------------------------------------------
    def is_draft(self) -> bool:
        return self.status is RoutineStatus.DRAFT

    def is_pending_review(self) -> bool:
        return self.status is RoutineStatus.PENDING_REVIEW

    def is_approved(self) -> bool:
        return self.status is RoutineStatus.APPROVED

    def is_rejected(self) -> bool:
        return self.status is RoutineStatus.REJECTED

    def is_replaced(self) -> bool:
        return self.status is RoutineStatus.REPLACED

    def can_be_edited(self) -> bool:
        return self.status in (RoutineStatus.DRAFT, RoutineStatus.REJECTED)

    def __str__(self) -> str:
        return (
            f"Routine(id={self.id_routine}, program={self.id_workout_program}, "
            f"status={self.status.value})"
        )
