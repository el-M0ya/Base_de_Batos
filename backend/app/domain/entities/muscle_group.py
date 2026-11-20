"""Domain entity ``MuscleGroup`` (R11, catalog)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.exceptions.domain_exceptions import InvalidDomainValue


@dataclass(frozen=True)
class MuscleGroup:
    """Catalog entry that classifies an exercise by the muscle it trains.

    ``id_muscle_group`` is ``None`` until the repository persists the entry.
    """

    id_muscle_group: Optional[int]
    name: str

    def __post_init__(self) -> None:
        if self.id_muscle_group is not None and (
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
        if len(cleaned) > 100:
            raise InvalidDomainValue(
                "name", self.name, "a name with at most 100 characters"
            )
        object.__setattr__(self, "name", cleaned)

    @property
    def normalized_name(self) -> str:
        """Return a comparison key used to detect duplicate catalog names."""
        return self.name.casefold()

    def __str__(self) -> str:
        return f"MuscleGroup(id={self.id_muscle_group}, name={self.name!r})"
