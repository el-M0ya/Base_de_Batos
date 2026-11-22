"""In-memory routine consultation repository for application tests."""

from __future__ import annotations

from datetime import date

from app.domain.entities.authorisation import Authorisation
from app.domain.entities.routine import Routine
from app.domain.repositories.routine_consultation_repository import (
    RoutineConsultationRepository,
)


class InMemoryRoutineConsultationRepository(RoutineConsultationRepository):
    """Apply the same program and effective-authorization rules as SQL."""

    def __init__(
        self,
        routines: list[Routine] | None = None,
        authorisations: list[Authorisation] | None = None,
    ) -> None:
        self._routines = list(routines or [])
        self._authorisations = list(authorisations or [])

    async def is_authorized_for_program(
        self,
        id_trainer: int,
        id_workout_program: int,
        on_date: date,
    ) -> bool:
        return any(
            authorisation.id_trainer == id_trainer
            and authorisation.id_workout_program == id_workout_program
            and authorisation.is_active_on(on_date)
            for authorisation in self._authorisations
        )

    async def list_for_trainer(
        self,
        id_trainer: int,
        id_workout_program: int,
        on_date: date,
    ) -> list[Routine]:
        def serves(trainer_id: int) -> bool:
            return any(
                authorisation.id_trainer == trainer_id
                and authorisation.id_workout_program == id_workout_program
                and authorisation.is_active_on(on_date)
                for authorisation in self._authorisations
            )

        return sorted(
            (
                routine
                for routine in self._routines
                if routine.id_workout_program == id_workout_program
                and routine.id_trainer_creator != id_trainer
                and serves(id_trainer)
                and serves(routine.id_trainer_creator)
            ),
            key=lambda routine: (
                routine.creation_date,
                routine.id_routine or 0,
            ),
            reverse=True,
        )
