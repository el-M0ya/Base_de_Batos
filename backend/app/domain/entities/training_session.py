"""Domain Entitie ``TrainingSession`` """

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Optional

from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidSessionData,
    SessionNotAllowed,
)

if TYPE_CHECKING: 
    from app.domain.entities.assignment import Assignment


MIN_PERCEIVED_INTENSITY = 1
MAX_PERCEIVED_INTENSITY = 10


def _ensure_positive_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


def _ensure_date(value: object, field_name: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise InvalidDomainValue(field_name, value, "a date")


def _ensure_time(value: object, field_name: str) -> None:
    if not isinstance(value, time):
        raise InvalidDomainValue(field_name, value, "a time")


def _validate_perceived_intensity(value: object) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not MIN_PERCEIVED_INTENSITY <= value <= MAX_PERCEIVED_INTENSITY
    ):
        raise InvalidSessionData(
            f"'intensity_perceived' must be an integer between "
            f"{MIN_PERCEIVED_INTENSITY} and {MAX_PERCEIVED_INTENSITY}."
        )
    return value


@dataclass
class TrainingSession:
    id_assignment: int
    start_time: time
    end_time: time
    id_session: Optional[int] = None
    session_date: date = field(default_factory=date.today)
    intensity_perceived: Optional[int] = None
    completed: bool = False
    observations: Optional[str] = None

    def __post_init__(self) -> None:
        self._validate_fields()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate_fields(self) -> None:
        _ensure_positive_int(self.id_assignment, "id_assignment")
        _ensure_date(self.session_date, "session_date")
        _ensure_time(self.start_time, "start_time")
        _ensure_time(self.end_time, "end_time")

        if self.id_session is not None:
            _ensure_positive_int(self.id_session, "id_session")

        if self.end_time < self.start_time:
            raise InvalidSessionData(
                "'end_time' can't be before 'start_time'."
            )

        if self.intensity_perceived is not None:
            _validate_perceived_intensity(self.intensity_perceived)

        if not isinstance(self.completed, bool):
            raise InvalidDomainValue("completed", self.completed, "a boolean")

        self.observations = self._normalise_observations(self.observations)

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

    def validate(self) -> None:
        self._validate_fields()

    # ------------------------------------------------------------------
    # Rules for the assignation
    # ------------------------------------------------------------------
    def validate_for(self, assignment: "Assignment") -> None:
        if (
            assignment.id_assignment is not None
            and assignment.id_assignment != self.id_assignment
        ):
            raise SessionNotAllowed(
                f"The session reference the assignation {self.id_assignment} but "
                f"was validated for {assignment.id_assignment}."
            )

        if self.session_date < assignment.assignment_date:
            raise SessionNotAllowed(
                f"The session ({self.session_date}) is before to the assignation "
                f"({assignment.assignment_date})."
            )

        if not assignment.is_active(self.session_date):
            raise SessionNotAllowed(
                f"The assignation {self.id_assignment} is not active in "
                f"{self.session_date}."
            )

    # ------------------------------------------------------------------
    # Life Cicle 
    # ------------------------------------------------------------------
    def complete(
        self,
        intensity_perceived: Optional[int] = None,
        observations: Optional[str] = None,
    ) -> None:

        if intensity_perceived is not None:
            _validate_perceived_intensity(intensity_perceived)
            self.intensity_perceived = intensity_perceived

        if observations is not None:
            self.observations = self._normalise_observations(observations)

        self.completed = True

    def reopen(self) -> None:
        self.completed = False

    # ------------------------------------------------------------------
    # Consults
    # ------------------------------------------------------------------
    def duration_minutes(self) -> int:
        start = datetime.combine(self.session_date, self.start_time)
        end = datetime.combine(self.session_date, self.end_time)
        return int((end - start).total_seconds() // 60)

    def is_completed(self) -> bool:
        return self.completed

    def was_on(self, target_date: date) -> bool:
        _ensure_date(target_date, "target_date")
        return self.session_date == target_date

    def __str__(self) -> str:
        return (
            f"TrainingSession(id={self.id_session}, "
            f"assignment={self.id_assignment}, date={self.session_date})"
        )
