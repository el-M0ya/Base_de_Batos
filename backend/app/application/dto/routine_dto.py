"""DTOs for program-scoped routine consultation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.application.dto.actor import ActorDTO
from app.domain.entities.routine import Routine
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


@dataclass(frozen=True)
class ListRoutinesForTrainerInputDTO:
    """Input required to consult routines from another trainer."""

    actor: ActorDTO
    id_workout_program: int
    on_date: Optional[date] = None

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        if (
            not isinstance(self.id_workout_program, int)
            or isinstance(self.id_workout_program, bool)
            or self.id_workout_program <= 0
        ):
            raise InvalidDomainValue(
                "id_workout_program",
                self.id_workout_program,
                "an integer greater than 0",
            )
        if self.on_date is not None and not isinstance(self.on_date, date):
            raise InvalidDomainValue("on_date", self.on_date, "a date")


@dataclass(frozen=True)
class RoutineSummaryDTO:
    """Routine metadata exposed by the consultation query."""

    id_routine: int
    id_workout_program: int
    id_trainer_creator: int
    creation_date: date
    status: str

    @classmethod
    def from_entity(cls, routine: Routine) -> "RoutineSummaryDTO":
        if routine.id_routine is None:
            raise InvalidDomainValue(
                "id_routine", routine.id_routine, "a persisted routine"
            )
        return cls(
            id_routine=routine.id_routine,
            id_workout_program=routine.id_workout_program,
            id_trainer_creator=routine.id_trainer_creator,
            creation_date=routine.creation_date,
            status=routine.status.value,
        )
