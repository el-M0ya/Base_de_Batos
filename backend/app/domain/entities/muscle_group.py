"""Domain entity ``MuscleGroup`` (R11, catalog)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions.domain_exceptions import InvalidDomainValue


@dataclass(frozen=True)
class MuscleGroup:
    """Catalog entry that classifies an exercise by the muscle it trains."""

    id_muscle_group: int
    name: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.id_muscle_group, int)
            or isinstance(self.id_muscle_group, bool)
            or self.id_muscle_group <= 0
        ):
            raise InvalidDomainValue(
                "id_muscle_group", self.id_muscle_group, "an integer greater than 0"
            )
        if not isinstance(self.name, str):
            raise InvalidDomainValue("name", self.name, "a non-empty name")
        cleaned = " ".join(self.name.split())
        if not cleaned:
            raise InvalidDomainValue("name", self.name, "a non-empty name")
        object.__setattr__(self, "name", cleaned)

    def __str__(self) -> str:
        return f"MuscleGroup(id={self.id_muscle_group}, name={self.name!r})"
