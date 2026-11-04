"""Domain Entitie ``Assignment`` """

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from app.domain.exceptions.domain_exceptions import (
    AssignmentNotAllowed,
    InvalidDateRange,
    InvalidDomainValue,
)

if TYPE_CHECKING:
    from app.domain.entities.routine import Routine


def _ensure_positive_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


def _ensure_date(value: object, field_name: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise InvalidDomainValue(field_name, value, "a date")


@dataclass
class Assignment:
    id_routine: int
    id_client: int
    id_assignment: Optional[int] = None
    assignment_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None

    def __post_init__(self) -> None:
        self._validate_fields()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate_fields(self) -> None:
        _ensure_positive_int(self.id_routine, "id_routine")
        _ensure_positive_int(self.id_client, "id_client")
        _ensure_date(self.assignment_date, "assignment_date")

        if self.id_assignment is not None:
            _ensure_positive_int(self.id_assignment, "id_assignment")

        if self.end_date is not None:
            _ensure_date(self.end_date, "end_date")
            if self.end_date < self.assignment_date:
                raise InvalidDateRange(
                    "assignment_date", "end_date", self.assignment_date, self.end_date
                )

    def validate(self) -> None:
        self._validate_fields()

    # ------------------------------------------------------------------
    # Life Cicle
    # ------------------------------------------------------------------
    def is_active(self, on: Optional[date] = None) -> bool:
        reference = on or date.today()
        _ensure_date(reference, "on")

        if reference < self.assignment_date:
            return False
        if self.end_date is None:
            return True
        return reference <= self.end_date

    def close(self, end_date: Optional[date] = None) -> None:
        closing = end_date or date.today()
        _ensure_date(closing, "end_date")
        if closing < self.assignment_date:
            raise InvalidDateRange(
                "assignment_date", "end_date", self.assignment_date, closing
            )
        self.end_date = closing

    def reopen(self) -> None:
        self.end_date = None

    def duration_days(self) -> Optional[int]:
        if self.end_date is None:
            return None
        return (self.end_date - self.assignment_date).days

    # ------------------------------------------------------------------
    # Rules for the routines and the clients
    # ------------------------------------------------------------------
    def validate_for(self, routine: "Routine", client_is_inscribed: bool) -> None:
        if routine.id_routine is not None and routine.id_routine != self.id_routine:
            raise AssignmentNotAllowed(
                f"The assignation reference the routine {self.id_routine} but "
                f"validate the routine {routine.id_routine}."
            )

        if not client_is_inscribed:
            raise AssignmentNotAllowed(
                f"The client {self.id_client} are not inscribed in the program"
                f"of the routine {self.id_routine}."
            )

    def __str__(self) -> str:
        return (
            f"Assignment(id={self.id_assignment}, routine={self.id_routine}, "
            f"client={self.id_client})"
        )
