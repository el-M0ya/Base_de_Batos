"""DTOs for routine retrieval (issue E6-03).

The input DTO keeps the request minimal: the authenticated actor and the
routine identifier. The output reuses ``GeneratedRoutineOutputDTO`` from the
generation module, because both operations expose the same aggregate shape
(routine header, generation parameters, composition, and JSONB structure).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.actor import ActorDTO
from app.domain.entities.routine import Routine
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


@dataclass(frozen=True)
class GetRoutineInputDTO:
    """Request to retrieve a complete routine by its identifier."""

    actor: ActorDTO
    id_routine: int

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        if (
            not isinstance(self.id_routine, int)
            or isinstance(self.id_routine, bool)
            or self.id_routine <= 0
        ):
            raise InvalidDomainValue(
                "id_routine", self.id_routine, "an integer greater than 0"
            )
