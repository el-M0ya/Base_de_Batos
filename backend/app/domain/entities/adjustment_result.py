"""Domain Entitie ``AdjustmentResult`` """

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from app.domain.entities.adjustment_request import RequestStatus
from app.domain.exceptions.domain_exceptions import (
    AdjustmentResultNotAllowed,
    AdjustmentTrainerMismatch,
    InvalidDomainValue,
    ResultBeforeRequest,
)

if TYPE_CHECKING:
    from app.domain.entities.adjustment_request import AdjustmentRequest


def _ensure_positive_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


def _ensure_date(value: object, field_name: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise InvalidDomainValue(field_name, value, "a date")


@dataclass
class AdjustmentResult:
    id_request: int
    id_trainer_resolver: int
    adjustment_description: str
    response_date: date = field(default_factory=date.today)
    id_routine_resulting: Optional[int] = None

    def __post_init__(self) -> None:
        self.validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _normalise_description(value: object) -> str:
        if not isinstance(value, str):
            raise InvalidDomainValue(
                "adjustment_description", value, "a text string"
            )
        stripped = value.strip()
        if not stripped:
            raise InvalidDomainValue(
                "adjustment_description", value, "a not empty string"
            )
        return stripped

    def _validate_fields(self) -> None:
        _ensure_positive_int(self.id_request, "id_request")
        _ensure_positive_int(self.id_trainer_resolver, "id_trainer_resolver")
        _ensure_date(self.response_date, "response_date")

        if self.id_routine_resulting is not None:
            _ensure_positive_int(self.id_routine_resulting, "id_routine_resulting")

    def validate(self) -> None:
        self.adjustment_description = self._normalise_description(self.adjustment_description)
        self._validate_fields()

    # ------------------------------------------------------------------
    # Rules for the request
    # ------------------------------------------------------------------
    def validate_for(self, request: "AdjustmentRequest") -> None:
        if request.id_request is not None and request.id_request != self.id_request:
            raise AdjustmentResultNotAllowed(
                f"The result is in the request {self.id_request} but "
                f"was validated in the request {request.id_request}."
            )

        if request.status is RequestStatus.CANCELLED:
            raise AdjustmentResultNotAllowed(
                f"The request {self.id_request} is cancelled. "
            )

        if request.status is RequestStatus.RESOLVED:
            raise AdjustmentResultNotAllowed(f"The request {self.id_request} alredy have result.")

        if self.id_trainer_resolver != request.id_trainer:
            raise AdjustmentTrainerMismatch(request.id_trainer, self.id_trainer_resolver)

        if self.response_date < request.request_date:
            raise ResultBeforeRequest(self.response_date, request.request_date)

        if (
            self.id_routine_resulting is not None
            and self.id_routine_resulting == request.id_routine
        ):
            raise AdjustmentResultNotAllowed(
                "The resulting routine has to be different to the routine "
                f"{request.id_routine} than wanted to be ajustment."
            )

    # ------------------------------------------------------------------
    # Effect for the request
    # ------------------------------------------------------------------
    def resolve_request(self, request: "AdjustmentRequest") -> None:
        self.validate_for(request)
        request.resolve()

    # ------------------------------------------------------------------
    # Consults
    # ------------------------------------------------------------------
    def creates_new_routine(self) -> bool:
        return self.id_routine_resulting is not None

    def is_for_request(self, id_request: int) -> bool:
        _ensure_positive_int(id_request, "id_request")
        return self.id_request == id_request

    def __str__(self) -> str:
        return (
            f"AdjustmentResult(request={self.id_request}, "
            f"trainer={self.id_trainer_resolver})"
        )
