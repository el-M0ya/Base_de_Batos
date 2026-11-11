"""Domain contract for routine adjustment requests and results."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.adjustment_request import AdjustmentRequest
from app.domain.entities.adjustment_result import AdjustmentResult


class AdjustmentRepository(ABC):
    """Persistence operations for adjustment workflows."""

    @abstractmethod
    async def save_request(
        self, request: AdjustmentRequest
    ) -> AdjustmentRequest:
        """Persist an adjustment request and return it."""

    @abstractmethod
    async def find_pending_for_client_and_routine(
        self, id_client: int, id_routine: int
    ) -> Optional[AdjustmentRequest]:
        """Return a client's pending request for a routine, or ``None``."""

    @abstractmethod
    async def save_result(self, result: AdjustmentResult) -> AdjustmentResult:
        """Persist an adjustment result and return it."""
