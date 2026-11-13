"""Use case for listing the training programs a client is enrolled in."""

from __future__ import annotations

from app.application.dto.enrolment_dto import EnrolmentOutputDTO
from app.application.exceptions import ResourceNotFound
from app.domain.repositories.enrolment_repository import EnrolmentRepository


class ListClientEnrolmentsUseCase:
    def __init__(self, enrolment_repository: EnrolmentRepository) -> None:
        self._enrolments = enrolment_repository

    async def execute(self, id_client: int) -> tuple[EnrolmentOutputDTO, ...]:
        if not isinstance(id_client, int) or isinstance(id_client, bool) or id_client <= 0:
            from app.application.exceptions import InvalidInput

            raise InvalidInput("id_client must be an integer greater than 0")
        if not await self._enrolments.client_exists(id_client):
            raise ResourceNotFound("client", id_client)
        rows = await self._enrolments.list_for_client(id_client)
        return tuple(EnrolmentOutputDTO.from_entity(item) for item in rows)
