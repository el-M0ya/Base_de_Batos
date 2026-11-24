"""Dedicated read contract for the first three informational reports."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.informational_report_dto import (
    ExerciseUsageByProgramQuery,
    ExerciseUsageReportRow,
    GeneratedRoutineReportRow,
    RoutinesByProgramQuery,
    ValidatedRoutineReportRow,
    ValidationsByReviewerQuery,
)


class InformationalReportsQuery(ABC):
    """Read-only report queries, separate from aggregate repositories."""

    @abstractmethod
    async def routines_by_program(
        self, query: RoutinesByProgramQuery
    ) -> tuple[GeneratedRoutineReportRow, ...]:
        """REP-01: list program routines with creator and generation snapshot."""

    @abstractmethod
    async def exercise_usage_by_program(
        self, query: ExerciseUsageByProgramQuery
    ) -> tuple[ExerciseUsageReportRow, ...]:
        """REP-02: count exercise use in final routines by intensity and muscle."""

    @abstractmethod
    async def validations_by_reviewer(
        self, query: ValidationsByReviewerQuery
    ) -> tuple[ValidatedRoutineReportRow, ...]:
        """REP-03: list review events and observations for a reviewer."""
