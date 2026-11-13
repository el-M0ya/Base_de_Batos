"""Use case for enrolling a client in a workout program."""

from __future__ import annotations

from datetime import date

from app.application.dto.enrolment_dto import (
    CreateEnrolmentInputDTO,
    EnrolmentOutputDTO,
    validate_enrolment_input,
)
from app.application.exceptions import DuplicateResource, InvalidInput, ResourceNotFound
from app.domain.entities.enrolment import Enrolment
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.enrolment_repository import EnrolmentRepository


class CreateEnrolmentUseCase:
    def __init__(self, enrolment_repository: EnrolmentRepository) -> None:
        self._enrolments = enrolment_repository

    async def execute(self, input_dto: CreateEnrolmentInputDTO) -> EnrolmentOutputDTO:
        try:
            validate_enrolment_input(input_dto)
        except DomainException as error:
            raise InvalidInput(str(error)) from error
        if not await self._enrolments.client_exists(input_dto.id_client):
            raise ResourceNotFound("client", input_dto.id_client)
        if not await self._enrolments.workout_program_exists(input_dto.id_workout_program):
            raise ResourceNotFound("workout program", input_dto.id_workout_program)
        existing = await self._enrolments.get(
            input_dto.id_client, input_dto.id_workout_program
        )
        if existing is not None:
            raise DuplicateResource(
                "enrollment",
                "the client is already enrolled in this workout program",
                existing=existing,
            )
        try:
            enrolment = Enrolment(
                id_client=input_dto.id_client,
                id_workout_program=input_dto.id_workout_program,
                enrollment_date=input_dto.enrollment_date or date.today(),
            )
        except DomainException as error:
            raise InvalidInput(str(error)) from error
        saved = await self._enrolments.create(enrolment)
        return EnrolmentOutputDTO.from_entity(saved)
