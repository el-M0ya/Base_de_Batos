"""Filter and result DTOs for informational reports REP-01 through REP-03."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.domain.exceptions.domain_exceptions import InvalidDomainValue


def _validate_filter_range(start_date: date | None, end_date: date | None) -> None:
    for name, value in (("start_date", start_date), ("end_date", end_date)):
        if value is not None and (
            not isinstance(value, date) or isinstance(value, datetime)
        ):
            raise InvalidDomainValue(name, value, "a date or None")
    if start_date is not None and end_date is not None and start_date > end_date:
        raise InvalidDomainValue(
            "date_range", (start_date, end_date), "start_date not after end_date"
        )


def _validate_identifier(name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(name, value, "a positive integer")


@dataclass(frozen=True)
class RoutinesByProgramQuery:
    id_workout_program: int
    start_date: date | None = None
    end_date: date | None = None

    def __post_init__(self) -> None:
        _validate_identifier("id_workout_program", self.id_workout_program)
        _validate_filter_range(self.start_date, self.end_date)


@dataclass(frozen=True)
class ExerciseUsageByProgramQuery:
    id_workout_program: int
    start_date: date | None = None
    end_date: date | None = None

    def __post_init__(self) -> None:
        _validate_identifier("id_workout_program", self.id_workout_program)
        _validate_filter_range(self.start_date, self.end_date)


@dataclass(frozen=True)
class ValidationsByReviewerQuery:
    id_reviewer: int
    start_date: date | None = None
    end_date: date | None = None

    def __post_init__(self) -> None:
        _validate_identifier("id_reviewer", self.id_reviewer)
        _validate_filter_range(self.start_date, self.end_date)


@dataclass(frozen=True)
class GeneratedRoutineReportRow:
    id_routine: int
    status: str
    id_trainer_creator: int
    trainer_name: str
    creation_date: date
    total_exercises: int
    intensity_level: str
    cardio_ratio: Decimal
    strength_ratio: Decimal
    flexibility_ratio: Decimal
    covered_muscle_group_ids: tuple[int, ...]


@dataclass(frozen=True)
class ExerciseUsageReportRow:
    id_exercise: int
    exercise_name: str
    routine_intensity: str
    id_muscle_group: int
    muscle_group_name: str
    usage_count: int


@dataclass(frozen=True)
class ValidatedRoutineReportRow:
    id_validation: int
    id_routine: int
    id_reviewer: int
    reviewer_name: str
    validation_date: date
    decision: str
    observations: str | None
