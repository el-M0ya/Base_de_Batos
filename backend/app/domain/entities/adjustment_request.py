"""Domain Entitie ``AdjustmentRequest`` """

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional

from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidRequestStateTransition,
    PendingRequestAlreadyExists,
    RequestNotAllowed,
)


class RequestStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


_ALLOWED_TRANSITIONS: dict[RequestStatus, frozenset[RequestStatus]] = {
    RequestStatus.PENDING: frozenset(
        {RequestStatus.IN_PROGRESS, RequestStatus.RESOLVED, RequestStatus.CANCELLED}
    ),
    RequestStatus.IN_PROGRESS: frozenset(
        {RequestStatus.RESOLVED, RequestStatus.CANCELLED}
    ),
    RequestStatus.RESOLVED: frozenset(),
    RequestStatus.CANCELLED: frozenset(),
}


def _ensure_positive_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


def _ensure_date(value: object, field_name: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise InvalidDomainValue(field_name, value, "a date")


@dataclass
class AdjustmentRequest:
    id_client: int
    id_routine: int
    id_trainer: int
    reason: str
    id_request: Optional[int] = None
    request_date: date = field(default_factory=date.today)
    status: RequestStatus = RequestStatus.PENDING

    def __post_init__(self) -> None:
        self.validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_status(value: object) -> RequestStatus:
        if isinstance(value, RequestStatus):
            return value
        try:
            return RequestStatus(value)  # type: ignore[arg-type]
        except ValueError as exc:
            raise InvalidDomainValue(
                "status", value, f"one of {[s.value for s in RequestStatus]}"
            ) from exc

    @staticmethod
    def _normalise_reason(value: object) -> str:
        if not isinstance(value, str):
            raise InvalidDomainValue("reason", value, "a text string")
        stripped = value.strip()
        if not stripped:
            raise InvalidDomainValue("reason", value, "a not empty string")
        return stripped

    def _validate_fields(self) -> None:
        _ensure_positive_int(self.id_client, "id_client")
        _ensure_positive_int(self.id_routine, "id_routine")
        _ensure_positive_int(self.id_trainer, "id_trainer")
        _ensure_date(self.request_date, "request_date")

        if self.id_request is not None:
            _ensure_positive_int(self.id_request, "id_request")

    def validate(self) -> None:
        self.status = self._coerce_status(self.status)
        self.reason = self._normalise_reason(self.reason)
        self._validate_fields()

    # ------------------------------------------------------------------
    # Businesss rules
    # ------------------------------------------------------------------
    def validate_for(
        self,
        routine_is_assigned_to_client: bool,
        has_pending_request_for_same_routine: bool,
    ) -> None:

        if not routine_is_assigned_to_client:
            raise RequestNotAllowed(
                f"The routine {self.id_routine} is not assigned to the client "
                f"{self.id_client}."
            )

        if has_pending_request_for_same_routine:
            raise PendingRequestAlreadyExists(self.id_routine)

    # ------------------------------------------------------------------
    # Life Cicle
    # ------------------------------------------------------------------
    def _transition_to(self, target: RequestStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS[self.status]
        if target not in allowed:
            raise InvalidRequestStateTransition(self.status, target)
        self.status = target

    def can_transition_to(self, target: RequestStatus) -> bool:
        target = self._coerce_status(target)
        return target in _ALLOWED_TRANSITIONS[self.status]

    def start(self) -> None:
        self._transition_to(RequestStatus.IN_PROGRESS)

    def resolve(self) -> None:
        self._transition_to(RequestStatus.RESOLVED)

    def cancel(self) -> None:
        self._transition_to(RequestStatus.CANCELLED)

    # ------------------------------------------------------------------
    # Consults
    # ------------------------------------------------------------------
    def is_pending(self) -> bool:
        return self.status is RequestStatus.PENDING

    def is_in_progress(self) -> bool:
        return self.status is RequestStatus.IN_PROGRESS

    def is_resolved(self) -> bool:
        return self.status is RequestStatus.RESOLVED

    def is_cancelled(self) -> bool:
        return self.status is RequestStatus.CANCELLED

    def is_open(self) -> bool:
        return self.status in (RequestStatus.PENDING, RequestStatus.IN_PROGRESS)

    def __str__(self) -> str:
        return (
            f"AdjustmentRequest(id={self.id_request}, "
            f"routine={self.id_routine}, status={self.status.value})"
        )
