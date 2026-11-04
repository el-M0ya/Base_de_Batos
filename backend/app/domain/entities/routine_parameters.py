"""Domain Entitie ``RoutineParameters`` """

from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Iterable

from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidParameters,
)

class IntensityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

MAX_PERCENTAGE = Decimal("100")

def _ensure_positive_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


def _to_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise InvalidDomainValue(field_name, value, "a decimal number")
    if isinstance(value, (int, float, str)):
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise InvalidDomainValue(field_name, value, "a decimal number") from exc
    raise InvalidDomainValue(field_name, value, "a decimal number")


@dataclass
class RoutineParameters:
    id_routine: int
    total_exercises: int
    intensity_level: IntensityLevel
    cardio_ratio: Decimal
    strength_ratio: Decimal
    flexibility_ratio: Decimal = Decimal("0")
    covered_muscle_group_ids: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_intensity(value: object) -> IntensityLevel:
        if isinstance(value, IntensityLevel):
            return value
        try:
            return IntensityLevel(value)  # type: ignore[arg-type] 
        except ValueError as exc:
            raise InvalidDomainValue(
                "intensity_level",
                value,
                f"one of {[i.value for i in IntensityLevel]}",
            ) from exc

    @staticmethod
    def _normalise_muscle_group_ids(values: object) -> list[int]:
        if values is None:
            return []
        if not isinstance(values, (list, tuple, set, frozenset)):
            raise InvalidDomainValue(
                "covered_muscle_group_ids", values, "a colection of integer"
            )

        normalised: list[int] = []
        seen: set[int] = set()
        for value in values:
            _ensure_positive_int(value, "covered_muscle_group_ids")
            if value not in seen:
                seen.add(value)
                normalised.append(value)
        return normalised

    def validate(self) -> None:
        self.intensity_level = self._coerce_intensity(self.intensity_level)
        self.cardio_ratio = _to_decimal(self.cardio_ratio, "cardio_ratio")
        self.strength_ratio = _to_decimal(self.strength_ratio, "strength_ratio")
        self.flexibility_ratio = _to_decimal(
            self.flexibility_ratio, "flexibility_ratio"
        )
        self.covered_muscle_group_ids = self._normalise_muscle_group_ids(
            self.covered_muscle_group_ids
        )
        _ensure_positive_int(self.id_routine, "id_routine")
        _ensure_positive_int(self.total_exercises, "total_exercises")

        for field_name in ("cardio_ratio", "strength_ratio", "flexibility_ratio"):
            ratio = getattr(self, field_name)
            if ratio < 0:
                raise InvalidParameters(f"'{field_name}' can't be negative.")
            if ratio > MAX_PERCENTAGE:
                raise InvalidParameters(
                    f"'{field_name}' can't get over {MAX_PERCENTAGE}."
                )

        total = self.total_ratio()
        if total > MAX_PERCENTAGE:
            raise InvalidParameters(
                f"The sum of the proportions ({total}) overcomes "
                f"{MAX_PERCENTAGE}."
            )

    # ------------------------------------------------------------------
    # Consults
    # ------------------------------------------------------------------
    def total_ratio(self) -> Decimal:
        return self.cardio_ratio + self.strength_ratio + self.flexibility_ratio

    def remaining_ratio(self) -> Decimal:
        return MAX_PERCENTAGE - self.total_ratio()

    def is_complete(self) -> bool:
        return self.total_ratio() == MAX_PERCENTAGE

    def covers(self, id_muscle_group: int) -> bool:
        return id_muscle_group in self.covered_muscle_group_ids

    def covers_all(self, id_muscle_groups: Iterable[int]) -> bool:
        return set(id_muscle_groups).issubset(set(self.covered_muscle_group_ids))
