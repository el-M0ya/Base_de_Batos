"""Strategy contract for interchangeable routine-generation algorithms.

The domain owns the contract and the data exchanged with the algorithms, but
not the concrete selection heuristics. Concrete strategies can therefore be
added or replaced without changing ``Routine`` or the use cases that request a
generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.routine_structure import RoutineBlock
from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidParameters,
)
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel


def _ensure_positive_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


def _ensure_non_negative_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise InvalidDomainValue(
            field_name, value, "an integer greater than or equal to 0"
        )


def _to_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise InvalidDomainValue(field_name, value, "a decimal number")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float, str)):
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise InvalidDomainValue(field_name, value, "a decimal number") from exc
    raise InvalidDomainValue(field_name, value, "a decimal number")


def _as_tuple_of(
    value: object, expected_type: type, field_name: str
) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise InvalidDomainValue(field_name, value, "a sequence")
    items = tuple(value)
    for item in items:
        if not isinstance(item, expected_type):
            raise InvalidDomainValue(
                field_name,
                item,
                f"instances of {expected_type.__name__}",
            )
    return items


@dataclass(frozen=True)
class RoutineGenerationRequest:
    """Input required by any routine-generation strategy.

    ``exercise_type_proportions`` expresses fractions in the closed interval
    [0, 1] whose sum must be exactly 1. This is intentionally separate from the
    percentage-based ``RoutineParameters`` model: the strategy contract uses
    proportions because they are independent from the UI representation.
    """

    candidate_exercises: Sequence[Exercise]
    target_intensity: IntensityLevel
    exercise_type_proportions: Mapping[ExerciseType, Decimal]
    total_exercises: int
    covered_muscle_groups: Sequence[MuscleGroup]

    def __post_init__(self) -> None:
        candidates = _as_tuple_of(self.candidate_exercises, Exercise, "candidate_exercises")
        if not candidates:
            raise InvalidParameters("at least one candidate exercise is required")
        object.__setattr__(self, "candidate_exercises", candidates)

        object.__setattr__(
            self,
            "target_intensity",
            IntensityLevel.from_value(self.target_intensity),
        )
        object.__setattr__(
            self,
            "covered_muscle_groups",
            _as_tuple_of(
                self.covered_muscle_groups,
                MuscleGroup,
                "covered_muscle_groups",
            ),
        )

        _ensure_positive_int(self.total_exercises, "total_exercises")

        if not isinstance(self.exercise_type_proportions, Mapping):
            raise InvalidDomainValue(
                "exercise_type_proportions",
                self.exercise_type_proportions,
                "a mapping from ExerciseType to Decimal",
            )

        normalised: dict[ExerciseType, Decimal] = {}
        for key, raw_proportion in self.exercise_type_proportions.items():
            exercise_type = ExerciseType.from_value(key)
            proportion = _to_decimal(
                raw_proportion,
                f"exercise_type_proportions[{exercise_type.value!r}]",
            )
            if not proportion.is_finite() or proportion < 0 or proportion > 1:
                raise InvalidParameters(
                    "each exercise type proportion must be between 0 and 1"
                )
            if exercise_type in normalised:
                raise InvalidParameters(
                    f"exercise type {exercise_type.value!r} appears more than once"
                )
            normalised[exercise_type] = proportion

        if not normalised:
            raise InvalidParameters("at least one exercise type proportion is required")

        total_proportion = sum(normalised.values(), Decimal("0"))
        if total_proportion != Decimal("1"):
            raise InvalidParameters(
                f"exercise type proportions must sum to 1, got {total_proportion}"
            )

        object.__setattr__(self, "exercise_type_proportions", normalised)


@dataclass(frozen=True)
class GeneratedExercise:
    """One exercise selected by a strategy, before it becomes a block."""

    exercise: Exercise
    order: int
    sets: int
    repetitions: int
    rest_seconds: int

    def __post_init__(self) -> None:
        if not isinstance(self.exercise, Exercise):
            raise InvalidDomainValue("exercise", self.exercise, "an Exercise instance")
        _ensure_positive_int(self.order, "order")
        _ensure_positive_int(self.sets, "sets")
        _ensure_positive_int(self.repetitions, "repetitions")
        _ensure_non_negative_int(self.rest_seconds, "rest_seconds")


@dataclass(frozen=True)
class RoutineGenerationResult:
    """Selected exercises and the proposed JSONB block structure."""

    exercises: Sequence[GeneratedExercise]
    block_structure: Sequence[RoutineBlock]

    def __post_init__(self) -> None:
        exercises = _as_tuple_of(self.exercises, GeneratedExercise, "exercises")
        blocks = _as_tuple_of(self.block_structure, RoutineBlock, "block_structure")

        orders = [item.order for item in exercises]
        if len(orders) != len(set(orders)):
            raise InvalidParameters("generated exercise orders must be unique")

        object.__setattr__(self, "exercises", exercises)
        object.__setattr__(self, "block_structure", blocks)


class RoutineGenerationStrategy(ABC):
    """Interchangeable algorithm that proposes a routine for a program."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable name used to resolve the strategy from the registry."""

    @abstractmethod
    def generate(
        self, request: RoutineGenerationRequest
    ) -> RoutineGenerationResult:
        """Build a proposal from the request without persisting it."""
