"""DTOs for the routine review and validation-history use cases.

The review DTO carries the reviewer decision and the observations that the
database stores in the ``validate`` table. Approval observations are optional;
the domain requires non-empty observations for a rejection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from app.application.dto.actor import ActorDTO
from app.application.dto.muscle_group_dto import validate_actor, validate_positive_id
from app.domain.entities.routine import RoutineStatus
from app.domain.entities.routine_validation import RoutineValidation, ValidationDecision
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


@dataclass(frozen=True)
class ReviewRoutineInputDTO:
    """Data required to approve or reject a routine.

    ``decision`` accepts either the enum or its string value. ``validation_date``
    defaults to today; the domain rejects a date earlier than the routine
    creation date.
    """

    actor: ActorDTO
    id_routine: int
    decision: ValidationDecision | str
    observations: Optional[str] = None
    validation_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Validate the actor, identifiers, date, and decision shape."""
        validate_actor(self.actor)
        validate_positive_id("id_routine", self.id_routine)

        if not isinstance(self.validation_date, date) or isinstance(
            self.validation_date, datetime
        ):
            raise InvalidDomainValue(
                "validation_date", self.validation_date, "a date"
            )

        if not isinstance(self.decision, ValidationDecision):
            try:
                object.__setattr__(
                    self, "decision", ValidationDecision(self.decision)
                )
            except ValueError as error:
                raise InvalidDomainValue(
                    "decision",
                    self.decision,
                    f"one of {[decision.value for decision in ValidationDecision]}",
                ) from error

        if self.observations is not None and not isinstance(
            self.observations, str
        ):
            raise InvalidDomainValue(
                "observations", self.observations, "a text string or None"
            )


@dataclass(frozen=True)
class ListRoutineValidationsInputDTO:
    """Data required to retrieve the validation history of a routine."""

    actor: ActorDTO
    id_routine: int

    def __post_init__(self) -> None:
        """Validate the actor and routine identifier."""
        validate_actor(self.actor)
        validate_positive_id("id_routine", self.id_routine)


@dataclass(frozen=True)
class RoutineValidationOutputDTO:
    """Public representation of a persisted routine validation.

    ``id_room_chief`` is the identifier of the trainer who performed the
    review. ``routine_status`` is only populated when the output comes from a
    new review; history entries describe past decisions and therefore do not
    claim a current routine status.
    """

    id_validation: int
    id_routine: int
    id_room_chief: int
    decision: ValidationDecision
    validation_date: date
    observations: Optional[str] = None
    routine_status: Optional[RoutineStatus] = None

    @classmethod
    def from_entity(
        cls,
        validation: RoutineValidation,
        routine_status: Optional[RoutineStatus] = None,
    ) -> "RoutineValidationOutputDTO":
        """Map a persisted domain validation to the output DTO."""
        if validation.id_validation is None:
            raise InvalidDomainValue(
                "id_validation",
                validation.id_validation,
                "a persisted validation",
            )
        return cls(
            id_validation=validation.id_validation,
            id_routine=validation.id_routine,
            id_room_chief=validation.id_room_chief,
            decision=validation.decision,
            validation_date=validation.validation_date,
            observations=validation.observations,
            routine_status=routine_status,
        )
