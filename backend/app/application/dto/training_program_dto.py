"""DTOs for training program management and muscle-group coverage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from app.application.dto.actor import ActorDTO
from app.application.dto.muscle_group_dto import (
    MuscleGroupOutputDTO,
    validate_actor,
    validate_positive_id,
)
from app.domain.entities.workout_program import WorkoutProgram
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


def _validate_text(field: str, value: object, max_length: Optional[int] = None) -> str:
    """Validate and normalize a required text field."""
    if not isinstance(value, str):
        raise InvalidDomainValue(field, value, "a non-empty text")
    cleaned = " ".join(value.split())
    if not cleaned:
        raise InvalidDomainValue(field, value, "a non-empty text")
    if max_length is not None and len(cleaned) > max_length:
        raise InvalidDomainValue(
            field, value, f"a text with at most {max_length} characters"
        )
    return cleaned


def _normalize_muscle_group_ids(values: Iterable[int]) -> tuple[int, ...]:
    """Validate identifiers and remove duplicates while preserving order."""
    normalized: list[int] = []
    seen: set[int] = set()
    for value in values:
        identifier = validate_positive_id("muscle_group_ids", value)
        if identifier not in seen:
            seen.add(identifier)
            normalized.append(identifier)
    return tuple(normalized)


@dataclass(frozen=True)
class TrainingProgramOutputDTO:
    """Public representation of a training program and its coverage."""

    id_workout_program: int
    name: str
    objective: str
    muscle_group_ids: tuple[int, ...]
    muscle_groups: tuple[MuscleGroupOutputDTO, ...]

    @classmethod
    def from_entity(cls, program: WorkoutProgram) -> "TrainingProgramOutputDTO":
        """Map a persisted domain entity to the output DTO."""
        if program.id_workout_program is None:
            raise InvalidDomainValue(
                "id_workout_program",
                program.id_workout_program,
                "a persisted workout program",
            )
        groups = sorted(
            program.target_muscle_groups,
            key=lambda group: (group.name.casefold(), group.id_muscle_group or 0),
        )
        return cls(
            id_workout_program=program.id_workout_program,
            name=program.name,
            objective=program.objective,
            muscle_group_ids=tuple(
                group.id_muscle_group
                for group in groups
                if group.id_muscle_group is not None
            ),
            muscle_groups=tuple(
                MuscleGroupOutputDTO.from_entity(group) for group in groups
            ),
        )


@dataclass(frozen=True)
class CreateTrainingProgramInputDTO:
    """Data required to create a training program."""

    actor: ActorDTO
    name: str
    objective: str
    muscle_group_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        validate_actor(self.actor)
        object.__setattr__(self, "name", _validate_text("name", self.name, 150))
        object.__setattr__(
            self, "objective", _validate_text("objective", self.objective)
        )
        object.__setattr__(
            self,
            "muscle_group_ids",
            _normalize_muscle_group_ids(self.muscle_group_ids),
        )


@dataclass(frozen=True)
class UpdateTrainingProgramInputDTO:
    """Data accepted to update a training program and its coverage."""

    actor: ActorDTO
    id_workout_program: int
    name: str
    objective: str
    muscle_group_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        validate_actor(self.actor)
        validate_positive_id("id_workout_program", self.id_workout_program)
        object.__setattr__(self, "name", _validate_text("name", self.name, 150))
        object.__setattr__(
            self, "objective", _validate_text("objective", self.objective)
        )
        object.__setattr__(
            self,
            "muscle_group_ids",
            _normalize_muscle_group_ids(self.muscle_group_ids),
        )


@dataclass(frozen=True)
class DeleteTrainingProgramInputDTO:
    """Data required to delete a training program."""

    actor: ActorDTO
    id_workout_program: int

    def __post_init__(self) -> None:
        validate_actor(self.actor)
        validate_positive_id("id_workout_program", self.id_workout_program)


@dataclass(frozen=True)
class SetTrainingProgramMuscleGroupsInputDTO:
    """Data required to replace the coverage of a training program."""

    actor: ActorDTO
    id_workout_program: int
    muscle_group_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        validate_actor(self.actor)
        validate_positive_id("id_workout_program", self.id_workout_program)
        object.__setattr__(
            self,
            "muscle_group_ids",
            _normalize_muscle_group_ids(self.muscle_group_ids),
        )
