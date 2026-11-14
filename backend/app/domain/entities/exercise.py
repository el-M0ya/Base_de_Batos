"""Domain entity ``Exercise`` of the exercise bank (R11, RF-11, RF-12, RF-14).

The entity models business invariants only:

* a name is mandatory and cannot exceed the physical column width;
* the classification (exercise type, intensity and muscle group) is mandatory;
* the creating trainer is part of the identity of the exercise;
* duplicate detection uses the **normalized name plus the muscle group** (U-12),
  so the same name in a different muscle group is a different exercise.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Optional

from app.domain.entities.muscle_group import MuscleGroup
from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel

MAX_NAME_LENGTH = 150


def normalize_exercise_name(name: str) -> str:
    """Return the duplicate-detection key of an exercise name (U-12).

    The normalization is: lowercase, remove diacritics and collapse whitespace.
    """
    if not isinstance(name, str):
        raise InvalidDomainValue("name", name, "a string")
    decomposed = unicodedata.normalize("NFKD", name)
    without_diacritics = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(without_diacritics.lower().split())


def _ensure_positive_int(value: object, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidDomainValue(field_name, value, "an integer greater than 0")


@dataclass(frozen=True)
class Exercise:
    """An exercise of the bank, authored and classified by a trainer."""

    name: str
    exercise_type: ExerciseType
    intensity: IntensityLevel
    muscle_group: MuscleGroup
    id_trainer_creator: int
    id_exercise: Optional[int] = None
    description: Optional[str] = None
    registration_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        cleaned_name = self._clean_name(self.name)
        object.__setattr__(self, "name", cleaned_name)
        object.__setattr__(
            self, "exercise_type", ExerciseType.from_value(self.exercise_type)
        )
        object.__setattr__(self, "intensity", IntensityLevel.from_value(self.intensity))
        if not isinstance(self.muscle_group, MuscleGroup):
            raise InvalidDomainValue(
                "muscle_group", self.muscle_group, "a MuscleGroup instance"
            )
        _ensure_positive_int(self.id_trainer_creator, "id_trainer_creator")
        if self.id_exercise is not None:
            _ensure_positive_int(self.id_exercise, "id_exercise")
        object.__setattr__(self, "description", self._clean_description(self.description))
        self._ensure_date(self.registration_date, "registration_date")

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _clean_name(name: object) -> str:
        if not isinstance(name, str):
            raise InvalidDomainValue("name", name, "a non-empty name")
        cleaned = " ".join(name.split())
        if not cleaned:
            raise InvalidDomainValue("name", name, "a non-empty name")
        if len(cleaned) > MAX_NAME_LENGTH:
            raise InvalidDomainValue(
                "name", name, f"at most {MAX_NAME_LENGTH} characters"
            )
        return cleaned

    @staticmethod
    def _clean_description(description: object) -> Optional[str]:
        if description is None:
            return None
        if not isinstance(description, str):
            raise InvalidDomainValue("description", description, "a string or None")
        cleaned = description.strip()
        return cleaned or None

    @staticmethod
    def _ensure_date(value: object, field_name: str) -> None:
        if not isinstance(value, date) or isinstance(value, datetime):
            raise InvalidDomainValue(field_name, value, "a date")

    # ------------------------------------------------------------------
    # Business behaviour
    # ------------------------------------------------------------------
    @property
    def normalized_name(self) -> str:
        """Key used to detect duplicates inside a muscle group."""
        return normalize_exercise_name(self.name)

    def is_authored_by(self, id_trainer: int) -> bool:
        """True when ``id_trainer`` created this exercise (RF-15)."""
        return self.id_trainer_creator == id_trainer

    def belongs_to_muscle_group(self, id_muscle_group: int) -> bool:
        return self.muscle_group.id_muscle_group == id_muscle_group

    def reclassify(
        self,
        *,
        exercise_type: object,
        intensity: object,
        muscle_group: MuscleGroup,
    ) -> "Exercise":
        """Return a copy with a new classification (RF-15).

        The identity, author, description and registration date are preserved.
        ``replace`` rebuilds the immutable entity, so the new catalog values are
        validated by ``__post_init__`` exactly like a newly created exercise.
        """
        return replace(
            self,
            exercise_type=exercise_type,
            intensity=intensity,
            muscle_group=muscle_group,
        )

    def __str__(self) -> str:
        return (
            f"Exercise(id={self.id_exercise}, name={self.name!r}, "
            f"type={self.exercise_type.value}, intensity={self.intensity.value}, "
            f"muscle_group={self.muscle_group.id_muscle_group})"
        )
