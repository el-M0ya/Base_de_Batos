"""List the sessions recorded for the authenticated client's assignment."""

from __future__ import annotations

from app.application.dto.actor import ActorDTO
from app.application.dto.training_session_dto import TrainingSessionOutputDTO
from app.application.exceptions import PermissionDenied, ResourceNotFound
from app.domain.repositories.assignment_repository import AssignmentRepository
from app.domain.repositories.session_repository import SessionRepository


class ListTrainingSessionsUseCase:
    def __init__(
        self,
        assignments: AssignmentRepository,
        sessions: SessionRepository,
    ) -> None:
        self._assignments = assignments
        self._sessions = sessions

    async def execute(
        self, actor: ActorDTO, id_assignment: int
    ) -> tuple[TrainingSessionOutputDTO, ...]:
        if not actor.is_client():
            raise PermissionDenied("only clients can consult their training sessions.")
        assignment = await self._assignments.get_by_id(id_assignment)
        if assignment is None:
            raise ResourceNotFound("assignment", id_assignment)
        if assignment.id_client != actor.id_user:
            raise PermissionDenied(
                "clients can consult sessions only for their own assignments."
            )
        rows = await self._sessions.list_by_assignment(id_assignment)
        return tuple(TrainingSessionOutputDTO.from_entity(row) for row in rows)
