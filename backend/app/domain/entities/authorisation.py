"""Domain entity for trainer permissions over workout programs."""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.exceptions.domain_exceptions import (
    InvalidDateRange,
    InvalidDomainValue,
)


def _ensure_positive_int(value: object, field_name: str) -> None:
    """Reject identifiers that cannot reference a persisted domain entity."""
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


def _ensure_date(value: object, field_name: str) -> None:
    """Reject values that are not calendar dates."""
    if not isinstance(value, date) or isinstance(value, datetime):
        raise InvalidDomainValue(field_name, value, "a date")


@dataclass(frozen=True)
class Authorisation:
    """Permission granted to a trainer for one workout program."""

    id_trainer: int
    id_workout_program: int
    can_generate: bool = False
    can_validate: bool = False
    start_date: date = field(default_factory=date.today)
    end_date: date | None = None

    def __post_init__(self) -> None:
        """Validate identifiers, permissions, and the authorization period."""
        _ensure_positive_int(self.id_trainer, "id_trainer")
        _ensure_positive_int(self.id_workout_program, "id_workout_program")
        if not isinstance(self.can_generate, bool):
            raise InvalidDomainValue("can_generate", self.can_generate, "a boolean")
        if not isinstance(self.can_validate, bool):
            raise InvalidDomainValue("can_validate", self.can_validate, "a boolean")
        if not self.can_generate and not self.can_validate:
            raise InvalidDomainValue(
                "permissions", (self.can_generate, self.can_validate),
                "at least one permission",
            )
        _ensure_date(self.start_date, "start_date")
        if self.end_date is not None:
            _ensure_date(self.end_date, "end_date")
            if self.end_date < self.start_date:
                raise InvalidDateRange(
                    "start_date", "end_date", self.start_date, self.end_date
                )

    def is_active_on(self, on_date: date) -> bool:
        """Return whether this authorization is active on the supplied date."""
        _ensure_date(on_date, "on_date")
        return self.start_date <= on_date and (
            self.end_date is None or on_date <= self.end_date
        )

    def allows_generation_on(self, on_date: date) -> bool:
        """Return whether routine generation is authorized on a date."""
        return self.can_generate and self.is_active_on(on_date)

    def allows_validation_on(self, on_date: date) -> bool:
        """Return whether routine validation is authorized on a date."""
        return self.can_validate and self.is_active_on(on_date)

    def is_generation_authorized(self, on_date: date) -> bool:
        """Return whether generation is authorized on a date."""
        return self.allows_generation_on(on_date)

    def is_validation_authorized(self, on_date: date) -> bool:
        """Return whether validation is authorized on a date."""
        return self.allows_validation_on(on_date)
