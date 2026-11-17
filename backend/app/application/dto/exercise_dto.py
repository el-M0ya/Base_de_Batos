"""DTOs of the exercise use cases.

All of them are immutable: use cases receive plain data and return new values
instead of mutating what the caller passed in.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.application.dto.actor import ActorDTO
from app.domain.entities.exercise import Exercise
from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.repositories.exercise_repository import ORDERING_FIELDS


@dataclass(frozen=True)
class CreateExerciseInputDTO:
    """Data required to register an exercise in the bank (RF-11, RF-12)."""

    actor: ActorDTO
    name: str
    exercise_type: str
    intensity: str
    muscle_group_id: int
    description: Optional[str] = None
    registration_date: Optional[date] = None

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        if (
            not isinstance(self.muscle_group_id, int)
            or isinstance(self.muscle_group_id, bool)
            or self.muscle_group_id <= 0
        ):
            raise InvalidDomainValue(
                "muscle_group_id", self.muscle_group_id, "an integer greater than 0"
            )


@dataclass(frozen=True)
class ReclassifyExerciseInputDTO:
    """Data required to reclassify an existing exercise (RF-15)."""

    actor: ActorDTO
    id_exercise: int
    exercise_type: str
    intensity: str
    muscle_group_id: int

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        if (
            not isinstance(self.id_exercise, int)
            or isinstance(self.id_exercise, bool)
            or self.id_exercise <= 0
        ):
            raise InvalidDomainValue(
                "id_exercise", self.id_exercise, "an integer greater than 0"
            )
        if (
            not isinstance(self.muscle_group_id, int)
            or isinstance(self.muscle_group_id, bool)
            or self.muscle_group_id <= 0
        ):
            raise InvalidDomainValue(
                "muscle_group_id", self.muscle_group_id, "an integer greater than 0"
            )
        if not isinstance(self.exercise_type, str) or not self.exercise_type.strip():
            raise InvalidDomainValue(
                "exercise_type", self.exercise_type, "a non-empty string"
            )
        if not isinstance(self.intensity, str) or not self.intensity.strip():
            raise InvalidDomainValue("intensity", self.intensity, "a non-empty string")


@dataclass(frozen=True)
class ExerciseOutputDTO:
    """Flat representation of an exercise returned to the caller."""

    id_exercise: int
    name: str
    description: Optional[str]
    registration_date: date
    exercise_type: str
    intensity: str
    muscle_group_id: int
    muscle_group_name: str
    trainer_id: int

    @classmethod
    def from_entity(cls, exercise: Exercise) -> "ExerciseOutputDTO":
        """Map a domain entity to the application output DTO."""
        if exercise.id_exercise is None:
            raise InvalidDomainValue(
                "id_exercise", exercise.id_exercise, "a persisted exercise"
            )
        return cls(
            id_exercise=exercise.id_exercise,
            name=exercise.name,
            description=exercise.description,
            registration_date=exercise.registration_date,
            exercise_type=exercise.exercise_type.value,
            intensity=exercise.intensity.value,
            muscle_group_id=exercise.muscle_group.id_muscle_group,
            muscle_group_name=exercise.muscle_group.name,
            trainer_id=exercise.id_trainer_creator,
        )


@dataclass(frozen=True)
class ListExercisesInputDTO:
    """Filters and ordering accepted by the exercise listing (RF-13)."""

    actor: ActorDTO
    muscle_group_id: Optional[int] = None
    exercise_type: Optional[str] = None
    intensity: Optional[str] = None
    order_by: str = ORDERING_FIELDS[0]
    descending: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        if self.muscle_group_id is not None and (
            not isinstance(self.muscle_group_id, int)
            or isinstance(self.muscle_group_id, bool)
            or self.muscle_group_id <= 0
        ):
            raise InvalidDomainValue(
                "muscle_group_id", self.muscle_group_id, "an integer greater than 0"
            )
        if not isinstance(self.order_by, str) or not self.order_by.strip():
            raise InvalidDomainValue(
                "order_by", self.order_by, f"one of {list(ORDERING_FIELDS)}"
            )


@dataclass(frozen=True)
class MuscleGroupDTO:
    """Catalog entry exposed to the exercise form selectors."""

    id_muscle_group: int
    name: str


@dataclass(frozen=True)
class CatalogOutputDTO:
    """Catalogs required by the exercise form selectors."""

    muscle_groups: tuple[MuscleGroupDTO, ...]
    exercise_types: tuple[str, ...]
    intensity_levels: tuple[str, ...]
