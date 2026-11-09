"""Exercise type value object (R11, RF-12).

The stored values are the ones seeded in the ``exercise_type`` catalog, while
the English aliases make the use cases readable from the API layer.
"""

from __future__ import annotations

from enum import Enum

from app.domain.exceptions.domain_exceptions import InvalidDomainValue


class ExerciseType(str, Enum):
    """Classification of an exercise according to the approved catalog."""

    STRENGTH = "fuerza"
    CARDIO = "cardio"
    FLEXIBILITY = "flexibilidad"

    @classmethod
    def from_value(cls, value: object) -> "ExerciseType":
        """Build the value object from a catalog value or its English alias."""
        return exercise_type_from_value(value)


_ALIASES: dict[str, ExerciseType] = {
    "fuerza": ExerciseType.STRENGTH,
    "strength": ExerciseType.STRENGTH,
    "cardio": ExerciseType.CARDIO,
    "flexibilidad": ExerciseType.FLEXIBILITY,
    "flexibility": ExerciseType.FLEXIBILITY,
}


def exercise_type_from_value(value: object) -> ExerciseType:
    """Build the value object from a catalog value or its English alias."""
    if isinstance(value, ExerciseType):
        return value
    if isinstance(value, str):
        candidate = value.strip().lower()
        if candidate in _ALIASES:
            return _ALIASES[candidate]
    raise InvalidDomainValue(
        "exercise_type", value, f"one of {[item.value for item in ExerciseType]}"
    )
