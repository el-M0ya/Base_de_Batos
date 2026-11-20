"""Input and output DTOs for routine replacement requests."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from app.application.dto.actor import ActorDTO
from app.application.dto.routine_generation_dto import GeneratedRoutineOutputDTO
from app.domain.entities.routine import Routine
from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.value_objects.intensity_level import IntensityLevel


@dataclass(frozen=True)
class ReplaceRoutineInputDTO:
    actor: ActorDTO
    id_routine: int
    strategy_name: str
    total_exercises: int
    target_intensity: IntensityLevel | str
    exercise_type_proportions: Mapping[str, Decimal | int | float | str]
    request_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        if (
            not isinstance(self.id_routine, int)
            or isinstance(self.id_routine, bool)
            or self.id_routine <= 0
        ):
            raise InvalidDomainValue("id_routine", self.id_routine, "a positive integer")
        if not isinstance(self.strategy_name, str) or not self.strategy_name.strip():
            raise InvalidDomainValue("strategy_name", self.strategy_name, "a non-empty string")
        if (
            not isinstance(self.total_exercises, int)
            or isinstance(self.total_exercises, bool)
            or self.total_exercises <= 0
        ):
            raise InvalidDomainValue("total_exercises", self.total_exercises, "a positive integer")
        if not isinstance(self.exercise_type_proportions, Mapping):
            raise InvalidDomainValue(
                "exercise_type_proportions", self.exercise_type_proportions,
                "a mapping from exercise type to proportion",
            )
        if not isinstance(self.request_date, date) or isinstance(self.request_date, datetime):
            raise InvalidDomainValue("request_date", self.request_date, "a date")
        object.__setattr__(self, "strategy_name", self.strategy_name.strip())
        object.__setattr__(
            self,
            "target_intensity",
            IntensityLevel.from_value(self.target_intensity),
        )
        object.__setattr__(self, "exercise_type_proportions", dict(self.exercise_type_proportions))


@dataclass(frozen=True)
class ReplaceRoutineOutputDTO:
    replaced_routine: Routine
    generated_successor: GeneratedRoutineOutputDTO
