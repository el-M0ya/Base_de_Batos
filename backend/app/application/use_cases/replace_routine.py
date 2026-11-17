"""Request a successor routine after an authorised room-chief review."""

from __future__ import annotations

from app.application.dto.actor import ActorDTO
from app.application.dto.routine_generation_dto import GenerateRoutineInputDTO
from app.application.dto.routine_replacement_dto import (
    ReplaceRoutineInputDTO,
    ReplaceRoutineOutputDTO,
)
from app.application.exceptions import BusinessRuleViolation, ResourceNotFound
from app.application.services.authorization import require_validation_authorisation
from app.application.use_cases.generate_routine import GenerateRoutineUseCase
from app.domain.entities.routine import RoutineStatus
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.authorisation_repository import AuthorisationRepository
from app.domain.repositories.routine_repository import RoutineRepository
from app.domain.value_objects.user_role import UserRole


class ReplaceRoutineUseCase:
    """Generate a linked successor and mark the reviewed routine as replaced.

    The HTTP adapter runs this use case inside one transaction. The E6-02
    generation use case and the source-status update therefore share the same
    transaction; a failure in either step rolls back both changes.
    """

    def __init__(
        self,
        routine_repository: RoutineRepository,
        authorisation_repository: AuthorisationRepository,
        generate_routine: GenerateRoutineUseCase,
    ) -> None:
        self._routines = routine_repository
        self._authorisations = authorisation_repository
        self._generate_routine = generate_routine

    async def execute(
        self, input_dto: ReplaceRoutineInputDTO
    ) -> ReplaceRoutineOutputDTO:
        loaded = await self._routines.get_complete(input_dto.id_routine)
        if loaded is None:
            raise ResourceNotFound("routine", input_dto.id_routine)
        source, _structure = loaded

        validations = await self._routines.list_validations(input_dto.id_routine)
        if not validations:
            raise BusinessRuleViolation(
                "a routine must have a completed review before it can be replaced."
            )

        await require_validation_authorisation(
            input_dto.actor,
            source.id_workout_program,
            input_dto.request_date,
            self._authorisations,
        )

        if source.id_routine is None:
            raise BusinessRuleViolation("only persisted routines can be replaced.")
        expected_status = source.status
        try:
            source.replace()
        except DomainException as error:
            raise BusinessRuleViolation(
                f"the routine cannot be replaced from {expected_status.value}."
            ) from error

        # The room chief requests the replacement. The trainer who created the
        # source routine performs generation through the established E6-02
        # authorization checks and remains the recorded routine creator.
        generator = ActorDTO(
            id_user=source.id_trainer_creator,
            role=UserRole.TRAINER,
        )
        generated = await self._generate_routine.execute(
            GenerateRoutineInputDTO(
                actor=generator,
                id_workout_program=source.id_workout_program,
                strategy_name=input_dto.strategy_name,
                total_exercises=input_dto.total_exercises,
                target_intensity=input_dto.target_intensity,
                exercise_type_proportions=input_dto.exercise_type_proportions,
                generation_date=input_dto.request_date,
                id_routine_origin=source.id_routine,
            )
        )

        replaced = await self._routines.mark_replaced(
            source.id_routine, expected_status
        )
        return ReplaceRoutineOutputDTO(
            replaced_routine=replaced,
            generated_successor=generated,
        )
