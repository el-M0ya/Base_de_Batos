"""In-memory implementation of ``WorkoutProgramRepository`` for unit tests."""

from __future__ import annotations

from datetime import date
from typing import Optional

from app.application.exceptions import BusinessRuleViolation
from app.domain.entities.authorisation import Authorisation
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.workout_program import WorkoutProgram
from app.domain.repositories.workout_program_repository import (
    WorkoutProgramRepository,
)


class InMemoryWorkoutProgramRepository(WorkoutProgramRepository):
    """Dictionary-backed training program repository."""

    def __init__(self, programs: Optional[list[WorkoutProgram]] = None) -> None:
        self._programs: dict[int, WorkoutProgram] = {}
        self._next_id = 1
        self.blocked_deletion_ids: set[int] = set()
        self.enrolled_clients: set[tuple[int, int]] = set()
        self.authorisations: dict[tuple[int, int], Authorisation] = {}
        for program in programs or []:
            if program.id_workout_program is None:
                raise ValueError("seed programs must be persisted")
            self._programs[program.id_workout_program] = program
            self._next_id = max(self._next_id, program.id_workout_program + 1)

    async def save(self, program: WorkoutProgram) -> WorkoutProgram:
        if program.id_workout_program is None:
            saved = WorkoutProgram(
                id_workout_program=self._next_id,
                name=program.name,
                objective=program.objective,
                target_muscle_groups=list(program.target_muscle_groups),
            )
            self._next_id += 1
        else:
            saved = WorkoutProgram(
                id_workout_program=program.id_workout_program,
                name=program.name,
                objective=program.objective,
                target_muscle_groups=list(program.target_muscle_groups),
            )
        self._programs[saved.id_workout_program] = saved
        return saved

    async def get_by_id(self, id_workout_program: int) -> Optional[WorkoutProgram]:
        return self._programs.get(id_workout_program)

    async def get_by_name(self, name: str) -> Optional[WorkoutProgram]:
        key = " ".join(name.split()).casefold()
        for program in self._programs.values():
            if program.normalized_name == key:
                return program
        return None

    async def list(self) -> list[WorkoutProgram]:
        return sorted(
            self._programs.values(), key=lambda program: program.name.casefold()
        )

    async def delete(self, id_workout_program: int) -> None:
        if id_workout_program in self.blocked_deletion_ids:
            raise BusinessRuleViolation(
                "the training program cannot be deleted because other records "
                "reference it."
            )
        self._programs.pop(id_workout_program, None)

    async def list_covered_muscle_groups(
        self, id_workout_program: int
    ) -> list[MuscleGroup]:
        program = self._programs.get(id_workout_program)
        if program is None:
            return []
        return list(program.target_muscle_groups)

    async def is_client_enrolled(
        self, id_client: int, id_workout_program: int, on_date: Optional[date] = None
    ) -> bool:
        return (id_client, id_workout_program) in self.enrolled_clients

    async def get_authorisation(
        self, id_trainer: int, id_workout_program: int
    ) -> Optional[Authorisation]:
        return self.authorisations.get((id_trainer, id_workout_program))
