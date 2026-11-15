"""Domain entity ``WorkoutProgram`` (R20/R21, RF-10, RI-05, RI-06)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from app.domain.entities.muscle_group import MuscleGroup
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


@dataclass
class WorkoutProgram:
    """Training program with a unique name, an objective and covered groups."""

    name: str
    objective: str
    id_workout_program: Optional[int] = None
    target_muscle_groups: List[MuscleGroup] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize values and enforce the program invariants."""
        if self.target_muscle_groups is None:
            self.target_muscle_groups = []
        self.validate()

    def validate(self) -> None:
        """Ensure the program has valid fields and covered muscle groups."""
        if self.id_workout_program is not None and (
            not isinstance(self.id_workout_program, int)
            or isinstance(self.id_workout_program, bool)
            or self.id_workout_program <= 0
        ):
            raise InvalidDomainValue(
                "id_workout_program",
                self.id_workout_program,
                "an integer greater than 0",
            )

        if not isinstance(self.name, str):
            raise InvalidDomainValue("name", self.name, "a non-empty name")
        cleaned_name = " ".join(self.name.split())
        if not cleaned_name:
            raise InvalidDomainValue("name", self.name, "a non-empty name")
        if len(cleaned_name) > 150:
            raise InvalidDomainValue(
                "name", self.name, "a name with at most 150 characters"
            )
        self.name = cleaned_name

        if not isinstance(self.objective, str):
            raise InvalidDomainValue(
                "objective", self.objective, "a non-empty objective"
            )
        cleaned_objective = " ".join(self.objective.split())
        if not cleaned_objective:
            raise InvalidDomainValue(
                "objective", self.objective, "a non-empty objective"
            )
        self.objective = cleaned_objective

        if not isinstance(self.target_muscle_groups, list) or any(
            not isinstance(group, MuscleGroup)
            for group in self.target_muscle_groups
        ):
            raise InvalidDomainValue(
                "target_muscle_groups",
                self.target_muscle_groups,
                "a list of MuscleGroup instances",
            )

    @property
    def normalized_name(self) -> str:
        """Return a comparison key used to detect duplicate program names."""
        return self.name.casefold()

    def covered_muscle_group_ids(self) -> list[int]:
        """Return the identifiers of the covered groups, ignoring unpersisted ones."""
        return [
            group.id_muscle_group
            for group in self.target_muscle_groups
            if group.id_muscle_group is not None
        ]
