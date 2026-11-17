"""Register a session for an assignment owned by the authenticated client."""

from __future__ import annotations

from app.application.dto.training_session_dto import (
    RegisterTrainingSessionInputDTO,
    TrainingSessionOutputDTO,
)
from app.application.exceptions import (
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.domain.entities.training_session import TrainingSession
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.assignment_repository import AssignmentRepository
from app.domain.repositories.session_repository import SessionRepository


class RegisterTrainingSessionUseCase:
    def __init__(
        self,
        assignments: AssignmentRepository,
        sessions: SessionRepository,
    ) -> None:
        self._assignments = assignments
        self._sessions = sessions

    async def execute(
        self, request: RegisterTrainingSessionInputDTO
    ) -> TrainingSessionOutputDTO:
        if not request.actor.is_client():
            raise PermissionDenied("only clients can register their training sessions.")

        assignment = await self._assignments.get_by_id(request.id_assignment)
        if assignment is None:
            raise ResourceNotFound("assignment", request.id_assignment)
        if assignment.id_client != request.actor.id_user:
            raise PermissionDenied(
                "clients can register sessions only for their own assignments."
            )

        try:
            session = TrainingSession(
                id_assignment=assignment.id_assignment or request.id_assignment,
                session_date=request.session_date,
                start_time=request.start_time,
                end_time=request.end_time,
                intensity_perceived=request.intensity_perceived,
                completed=request.completed,
                observations=request.observations,
            )
            session.validate_for(assignment)
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        if await self._sessions.find_by_assignment_and_date(
            request.id_assignment, request.session_date
        ):
            raise DuplicateResource(
                "session", "a session already exists for this assignment on this date"
            )

        saved = await self._sessions.save(session)
        if saved.id_session is None:
            raise InvalidInput("the session repository returned no identifier")
        return TrainingSessionOutputDTO.from_entity(saved)
