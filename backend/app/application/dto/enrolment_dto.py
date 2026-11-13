"""Input and output DTOs for client enrollment use cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.domain.entities.enrolment import Enrolment
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


@dataclass(frozen=True)
class CreateEnrolmentInputDTO:
    id_client: int
    id_workout_program: int
    enrollment_date: date | None = None


@dataclass(frozen=True)
class EnrolmentOutputDTO:
    id_client: int
    id_workout_program: int
    enrollment_date: date

    @classmethod
    def from_entity(cls, enrolment: Enrolment) -> "EnrolmentOutputDTO":
        return cls(
            id_client=enrolment.id_client,
            id_workout_program=enrolment.id_workout_program,
            enrollment_date=enrolment.enrollment_date,
        )


def validate_enrolment_input(input_dto: CreateEnrolmentInputDTO) -> None:
    """Validate IDs and optional date before repository access."""
    for field, value in (
        ("id_client", input_dto.id_client),
        ("id_workout_program", input_dto.id_workout_program),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise InvalidDomainValue(field, value, "an integer greater than 0")
    if input_dto.enrollment_date is not None and (
        not isinstance(input_dto.enrollment_date, date)
        or isinstance(input_dto.enrollment_date, datetime)
    ):
        raise InvalidDomainValue("enrollment_date", input_dto.enrollment_date, "a date")
