"""DTOs for muscle group catalog management."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.actor import ActorDTO
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


def validate_positive_id(field: str, value: object) -> int:
    """Validate an entity identifier and return it as an ``int``."""
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise InvalidDomainValue(field, value, "an integer greater than 0")
    return value


def validate_actor(actor: object) -> ActorDTO:
    """Validate that the value is an ``ActorDTO``."""
    if not isinstance(actor, ActorDTO):
        raise InvalidDomainValue("actor", actor, "an ActorDTO instance")
    return actor


def validate_name(value: object) -> str:
    """Validate a non-empty catalog name with the database length limit."""
    if not isinstance(value, str):
        raise InvalidDomainValue("name", value, "a non-empty name")
    cleaned = " ".join(value.split())
    if not cleaned:
        raise InvalidDomainValue("name", value, "a non-empty name")
    if len(cleaned) > 100:
        raise InvalidDomainValue(
            "name", value, "a name with at most 100 characters"
        )
    return cleaned


@dataclass(frozen=True)
class MuscleGroupOutputDTO:
    """Public representation of a muscle group catalog entry."""

    id_muscle_group: int
    name: str

    @classmethod
    def from_entity(cls, muscle_group: MuscleGroup) -> "MuscleGroupOutputDTO":
        """Map a persisted domain entity to the output DTO."""
        if muscle_group.id_muscle_group is None:
            raise InvalidDomainValue(
                "id_muscle_group",
                muscle_group.id_muscle_group,
                "a persisted muscle group",
            )
        return cls(
            id_muscle_group=muscle_group.id_muscle_group,
            name=muscle_group.name,
        )


@dataclass(frozen=True)
class CreateMuscleGroupInputDTO:
    """Data required to create a muscle group."""

    actor: ActorDTO
    name: str

    def __post_init__(self) -> None:
        validate_actor(self.actor)
        object.__setattr__(self, "name", validate_name(self.name))


@dataclass(frozen=True)
class UpdateMuscleGroupInputDTO:
    """Data accepted to rename an existing muscle group."""

    actor: ActorDTO
    id_muscle_group: int
    name: str

    def __post_init__(self) -> None:
        validate_actor(self.actor)
        validate_positive_id("id_muscle_group", self.id_muscle_group)
        object.__setattr__(self, "name", validate_name(self.name))


@dataclass(frozen=True)
class DeleteMuscleGroupInputDTO:
    """Data required to delete a muscle group."""

    actor: ActorDTO
    id_muscle_group: int

    def __post_init__(self) -> None:
        validate_actor(self.actor)
        validate_positive_id("id_muscle_group", self.id_muscle_group)
