"""Domain entity for client enrollment in a workout program."""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.exceptions.domain_exceptions import InvalidDomainValue


def _ensure_positive_int(value: object, field_name: str) -> None:
    """Reject identifiers that cannot reference a persisted domain entity."""
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


@dataclass(frozen=True)
class Enrolment:
    """Association between a client and a workout program."""

    id_client: int
    id_workout_program: int
    enrollment_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Validate the enrollment identifiers and date."""
        _ensure_positive_int(self.id_client, "id_client")
        _ensure_positive_int(self.id_workout_program, "id_workout_program")
        if not isinstance(self.enrollment_date, date) or isinstance(
            self.enrollment_date, datetime
        ):
            raise InvalidDomainValue(
                "enrollment_date", self.enrollment_date, "a date"
            )
