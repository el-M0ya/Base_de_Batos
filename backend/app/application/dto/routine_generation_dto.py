"""DTOs for the routine-generation use case (issue E6-02).

The input DTO keeps the generation criteria close to what the caller supplied.
The use case is the component that validates the count and the proportions, so
invalid criteria are reported as application ``InvalidInput`` errors instead of
domain exceptions.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from app.application.dto.actor import ActorDTO
from app.domain.entities.routine import Routine
from app.domain.entities.routine_parameters import RoutineParameters
from app.domain.entities.routine_structure import RoutineStructure
from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.strategies.routine_generation_strategy import GeneratedExercise
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel


def _ensure_positive_int(value: object, field_name: str) -> None:
    """Reject values that cannot identify a persisted aggregate."""
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


@dataclass(frozen=True)
class GenerateRoutineInputDTO:
    """Request that asks a trainer to generate a routine for a program.

    ``exercise_type_proportions`` maps an exercise type to its fraction of the
    requested exercises. The values are validated by the use case because the
    proportion rule (sum exactly 1) belongs to the generation criteria, not to
    the shape of the request.
    """

    actor: ActorDTO
    id_workout_program: int
    strategy_name: str
    total_exercises: int
    target_intensity: IntensityLevel | str
    exercise_type_proportions: Mapping[
        ExerciseType | str, Decimal | int | float | str
    ]
    generation_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        _ensure_positive_int(self.id_workout_program, "id_workout_program")
        if not isinstance(self.strategy_name, str) or not self.strategy_name.strip():
            raise InvalidDomainValue(
                "strategy_name", self.strategy_name, "a non-empty string"
            )
        if not isinstance(self.total_exercises, int) or isinstance(
            self.total_exercises, bool
        ):
            raise InvalidDomainValue(
                "total_exercises", self.total_exercises, "an integer"
            )
        if not isinstance(self.exercise_type_proportions, Mapping):
            raise InvalidDomainValue(
                "exercise_type_proportions",
                self.exercise_type_proportions,
                "a mapping from exercise type to proportion",
            )
        if not isinstance(self.generation_date, date) or isinstance(
            self.generation_date, datetime
        ):
            raise InvalidDomainValue("generation_date", self.generation_date, "a date")

        object.__setattr__(self, "strategy_name", self.strategy_name.strip())
        object.__setattr__(
            self,
            "target_intensity",
            IntensityLevel.from_value(self.target_intensity),
        )
        # Copy the mapping so later mutations by the caller cannot change the
        # request while the use case is running.
        object.__setattr__(
            self,
            "exercise_type_proportions",
            dict(self.exercise_type_proportions),
        )


@dataclass(frozen=True)
class GeneratedRoutineOutputDTO:
    """Application result of a successful generation and persistence.

    The routine is the persisted header, the parameters are the values attached
    to it, the composition is the ordered strategy selection, and the structure
    is the JSONB block document. Delivery adapters are responsible for mapping
    these domain objects to their own response representation.
    """

    routine: Routine
    parameters: RoutineParameters
    composition: tuple[GeneratedExercise, ...]
    structure: RoutineStructure
