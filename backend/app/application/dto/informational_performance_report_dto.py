"""DTOs for informational performance reports REP-04 through REP-06."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RoutinePerformanceQuery:
    id_routine: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.id_routine, int)
            or isinstance(self.id_routine, bool)
            or self.id_routine <= 0
        ):
            raise ValueError("id_routine must be a positive integer")


@dataclass(frozen=True)
class RoutinePerformanceRow:
    id_routine: int
    intensity_level: str | None
    id_client: int | None
    client_name: str | None
    exercise_ids: tuple[int, ...]
    exercise_names: tuple[str, ...]
    session_count: int
    completed_session_count: int
    completion_rate: Decimal | None


@dataclass(frozen=True)
class ProgramDistributionRow:
    id_workout_program: int
    program_name: str
    id_muscle_group: int | None
    muscle_group_name: str | None
    intensity_level: str | None
    exercise_count: int
    routine_count: int
    balance_criteria_met: bool | None
    balance_status: str


@dataclass(frozen=True)
class ProgramDistributionQuery:
    pass


@dataclass(frozen=True)
class IntensityPerformanceCorrelationRow:
    id_workout_program: int
    program_name: str
    correlation: float | None
    observation_count: int
    calculation_status: str


@dataclass(frozen=True)
class AdjustmentCohortComparisonRow:
    id_site: int
    site_name: str
    id_workout_program: int
    program_name: str
    adjustment_client_count: int
    adjustment_cohort_completion_rate: Decimal | None
    site_average_completion_rate: Decimal | None


@dataclass(frozen=True)
class AbandonmentRankingReport:
    available: bool
    status: str
    reason: str
    rows: tuple[object, ...] = ()
