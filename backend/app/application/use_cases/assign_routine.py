"""Use case for assigning a routine to a client (RF-28, R5, R6, U-9).

The checks and the insert use repositories bound to the same request
transaction, so a caller opening a ``TransactionManager`` block gets one atomic
unit of work. No approval status is required: the supplied requirements only
require the routine to exist and the client to be enrolled in its program.
"""

from __future__ import annotations

from app.application.dto.routine_assignment_dto import (
    AssignRoutineInputDTO,
    AssignmentOutputDTO,
)
from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    ResourceNotFound,
)
from app.domain.entities.assignment import Assignment
from app.domain.exceptions.domain_exceptions import (
    AssignmentNotAllowed,
    DomainException,
)
from app.domain.repositories.assignment_repository import AssignmentRepository
from app.domain.repositories.enrolment_repository import EnrolmentRepository
from app.domain.repositories.routine_repository import RoutineRepository


class AssignRoutineUseCase:
    """Assign a routine after validating all rules from RF-28."""

    def __init__(
        self,
        routine_repository: RoutineRepository,
        enrolment_repository: EnrolmentRepository,
        assignment_repository: AssignmentRepository,
    ) -> None:
        self._routines = routine_repository
        self._enrolments = enrolment_repository
        self._assignments = assignment_repository

    async def execute(
        self, input_dto: AssignRoutineInputDTO
    ) -> AssignmentOutputDTO:
        """Validate the assignment and persist it once every rule passes."""
        try:
            assignment = Assignment(
                id_routine=input_dto.id_routine,
                id_client=input_dto.id_client,
                assignment_date=input_dto.assignment_date,
                end_date=input_dto.end_date,
            )
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        loaded = await self._routines.get_complete(input_dto.id_routine)
        if loaded is None:
            raise ResourceNotFound("routine", input_dto.id_routine)
        routine, _structure = loaded

        if not await self._enrolments.client_exists(input_dto.id_client):
            raise ResourceNotFound("client", input_dto.id_client)

        enrolment = await self._enrolments.get(
            input_dto.id_client, routine.id_workout_program
        )
        try:
            assignment.validate_for(routine, enrolment is not None)
        except AssignmentNotAllowed as error:
            raise BusinessRuleViolation(str(error)) from error
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        existing = await self._assignments.find_by_routine_and_client(
            input_dto.id_routine, input_dto.id_client
        )
        if existing is not None:
            raise DuplicateResource(
                "assignment",
                "the routine has already been assigned to this client",
                existing=existing,
            )

        saved = await self._assignments.save(assignment)
        return AssignmentOutputDTO.from_entity(saved)
