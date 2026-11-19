"""In-memory implementation of ``MuscleGroupRepository`` for unit tests."""

from __future__ import annotations

from typing import Optional

from app.domain.entities.muscle_group import MuscleGroup
from app.domain.repositories.muscle_group_repository import MuscleGroupRepository


class InMemoryMuscleGroupRepository(MuscleGroupRepository):
    """Dictionary-backed muscle group repository."""

    def __init__(self, muscle_groups: Optional[list[MuscleGroup]] = None) -> None:
        self._muscle_groups: dict[int, MuscleGroup] = {}
        self._next_id = 1
        for muscle_group in muscle_groups or []:
            if muscle_group.id_muscle_group is None:
                raise ValueError("seed muscle groups must be persisted")
            self._muscle_groups[muscle_group.id_muscle_group] = muscle_group
            self._next_id = max(self._next_id, muscle_group.id_muscle_group + 1)

    async def save(self, muscle_group: MuscleGroup) -> MuscleGroup:
        if muscle_group.id_muscle_group is None:
            saved = MuscleGroup(
                id_muscle_group=self._next_id,
                name=muscle_group.name,
            )
            self._next_id += 1
        else:
            saved = MuscleGroup(
                id_muscle_group=muscle_group.id_muscle_group,
                name=muscle_group.name,
            )
        self._muscle_groups[saved.id_muscle_group] = saved
        return saved

    async def get_by_id(self, id_muscle_group: int) -> Optional[MuscleGroup]:
        return self._muscle_groups.get(id_muscle_group)

    async def get_by_name(self, name: str) -> Optional[MuscleGroup]:
        key = " ".join(name.split()).casefold()
        for muscle_group in self._muscle_groups.values():
            if muscle_group.normalized_name == key:
                return muscle_group
        return None

    async def list(self) -> list[MuscleGroup]:
        return sorted(
            self._muscle_groups.values(), key=lambda group: group.name.casefold()
        )

    async def delete(self, id_muscle_group: int) -> None:
        self._muscle_groups.pop(id_muscle_group, None)
