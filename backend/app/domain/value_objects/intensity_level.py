"""Intensity level value object (R11, RF-12).

The same value object is reused for exercise intensity, target intensity and
perceived intensity, as required by the design.
"""

from __future__ import annotations

from enum import Enum

from app.domain.exceptions.domain_exceptions import InvalidDomainValue


class IntensityLevel(str, Enum):
    """Intensity levels of the approved catalog."""

    LOW = "bajo"
    MEDIUM = "medio"
    HIGH = "alto"

    @classmethod
    def from_value(cls, value: object) -> "IntensityLevel":
        """Build the value object from a catalog value or its English alias."""
        return intensity_level_from_value(value)


_ALIASES: dict[str, IntensityLevel] = {
    "bajo": IntensityLevel.LOW,
    "low": IntensityLevel.LOW,
    "medio": IntensityLevel.MEDIUM,
    "medium": IntensityLevel.MEDIUM,
    "alto": IntensityLevel.HIGH,
    "high": IntensityLevel.HIGH,
}


def intensity_level_from_value(value: object) -> IntensityLevel:
    """Build the value object from a catalog value or its English alias."""
    if isinstance(value, IntensityLevel):
        return value
    if isinstance(value, str):
        candidate = value.strip().lower()
        if candidate in _ALIASES:
            return _ALIASES[candidate]
    raise InvalidDomainValue(
        "intensity", value, f"one of {[item.value for item in IntensityLevel]}"
    )
