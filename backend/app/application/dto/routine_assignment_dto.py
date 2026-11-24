"""Input and output DTOs for assigning a routine to a client (RF-28)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from app.domain.entities.assignment import Assignment
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


def _validate_positive_id(field_name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


def _validate_date(field_name: str, value: object) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise InvalidDomainValue(field_name, value, "a date")


@dataclass(frozen=True)
class AssignRoutineInputDTO:
    """Data required to assign an existing routine to an existing client.

    The start date defaults to today. The optional end date is validated by the
    ``Assignment`` entity, which rejects an end date before the start date.
    """

    id_routine: int
    id_client: int
    assignment_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None

    def __post_init__(self) -> None:
        _validate_positive_id("id_routine", self.id_routine)
        _validate_positive_id("id_client", self.id_client)
        _validate_date("assignment_date", self.assignment_date)
        if self.end_date is not None:
            _validate_date("end_date", self.end_date)


@dataclass(frozen=True)
class AssignmentOutputDTO:
    """Public representation of a persisted routine assignment."""

    id_assignment: int
    id_routine: int
    id_client: int
    assignment_date: date
    end_date: Optional[date] = None

    @classmethod
    def from_entity(cls, assignment: Assignment) -> "AssignmentOutputDTO":
        if assignment.id_assignment is None:
            raise InvalidDomainValue(
                "id_assignment",
                assignment.id_assignment,
                "a persisted assignment",
            )
        return cls(
            id_assignment=assignment.id_assignment,
            id_routine=assignment.id_routine,
            id_client=assignment.id_client,
            assignment_date=assignment.assignment_date,
            end_date=assignment.end_date,
        )
