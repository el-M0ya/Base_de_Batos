"""Read contract for routine performance and program comparison reports."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.informational_performance_report_dto import (
    AbandonmentRankingReport,
    AdjustmentCohortComparisonRow,
    IntensityPerformanceCorrelationRow,
    ProgramDistributionQuery,
    ProgramDistributionRow,
    RoutinePerformanceQuery,
    RoutinePerformanceRow,
)


class InformationalPerformanceReportsQuery(ABC):
    @abstractmethod
    async def routine_performance(
        self, query: RoutinePerformanceQuery
    ) -> tuple[RoutinePerformanceRow, ...]:
        """REP-04: exercise intensity and client completion per routine."""

    @abstractmethod
    async def program_distributions(
        self, query: ProgramDistributionQuery
    ) -> tuple[ProgramDistributionRow, ...]:
        """REP-05: program exercise distributions and unresolved balance state."""

    @abstractmethod
    async def intensity_performance_correlations(
        self,
    ) -> tuple[IntensityPerformanceCorrelationRow, ...]:
        """REP-06a: Pearson correlation using the project's ordinal intensity."""

    @abstractmethod
    async def exercise_abandonment_ranking(self) -> AbandonmentRankingReport:
        """REP-06b: explicit unavailable result until instructors define its rate."""

    @abstractmethod
    async def adjustment_cohort_comparisons(
        self,
    ) -> tuple[AdjustmentCohortComparisonRow, ...]:
        """REP-06c: compare adjustment clients with their site's program average."""
