"""Domain Entitie ``RoutineValidation`` """

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from app.domain.entities.routine import RoutineStatus
from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidValidationDate,
    RejectedValidationRequiresObservations,
    ValidationNotAllowed,
)

if TYPE_CHECKING: 
    from app.domain.entities.routine import Routine


class ValidationDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


def _ensure_positive_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


def _ensure_date(value: object, field_name: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise InvalidDomainValue(field_name, value, "a date")


@dataclass
class RoutineValidation:
    id_routine: int
    id_room_chief: int
    decision: ValidationDecision
    id_validation: Optional[int] = None
    validation_date: date = field(default_factory=date.today)
    observations: Optional[str] = None

    def __post_init__(self) -> None:
        self.validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_decision(value: object) -> ValidationDecision:
        if isinstance(value, ValidationDecision):
            return value
        try:
            return ValidationDecision(value)  # type: ignore[arg-type]
        except ValueError as exc:
            raise InvalidDomainValue(
                "decision", value, f"one of {[d.value for d in ValidationDecision]}"
            ) from exc

    @staticmethod
    def _normalise_observations(value: object) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidDomainValue(
                "observations", value, "a text string or None"
            )
        stripped = value.strip()
        return stripped or None

    def _validate_fields(self) -> None:
        _ensure_positive_int(self.id_routine, "id_routine")
        _ensure_positive_int(self.id_room_chief, "id_room_chief")
        _ensure_date(self.validation_date, "validation_date")

        if self.id_validation is not None:
            _ensure_positive_int(self.id_validation, "id_validation")

    def validate(self) -> None:
        self.decision = self._coerce_decision(self.decision)
        self.observations = self._normalise_observations(self.observations)
        self._validate_fields()
        if self.is_rejection() and self.observations is None:
            raise RejectedValidationRequiresObservations()

    # ------------------------------------------------------------------
    # Rules for the routines
    # ------------------------------------------------------------------
    def validate_for(self, routine: "Routine") -> None:
        if routine.id_routine is not None and routine.id_routine != self.id_routine:
            raise ValidationNotAllowed(
                f"The revision is in the routine {self.id_routine} but "
                f"try to apply the routine {routine.id_routine}."
            )

        if routine.status is not RoutineStatus.PENDING_REVIEW:
            raise ValidationNotAllowed(
                f"The routine {self.id_routine} is in state "
                f"'{routine.status.value}'; only can be validated in "
                f"'PENDING_REVIEW'."
            )

        if self.validation_date < routine.creation_date:
            raise InvalidValidationDate(
                self.validation_date, routine.creation_date
            )

    # ------------------------------------------------------------------
    # Consults
    # ------------------------------------------------------------------
    def is_approval(self) -> bool:
        return self.decision is ValidationDecision.APPROVED

    def is_rejection(self) -> bool:
        return self.decision is ValidationDecision.REJECTED

    def observations_are_required(self) -> bool:
        return self.is_rejection()

    def __str__(self) -> str:
        return (
            f"RoutineValidation(routine={self.id_routine}, "
            f"decision={self.decision.value})"
        )
