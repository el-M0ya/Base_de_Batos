"""In-memory enrollment repository for application use-case tests."""

from __future__ import annotations

from app.domain.entities.enrolment import Enrolment
from app.domain.repositories.enrolment_repository import EnrolmentRepository


class InMemoryEnrolmentRepository(EnrolmentRepository):
    def __init__(self, clients: set[int] | None = None, programs: set[int] | None = None):
        self.clients = set(clients or {1})
        self.programs = set(programs or {10, 11})
        self.enrolments: list[Enrolment] = []

    async def client_exists(self, id_client: int) -> bool:
        return id_client in self.clients

    async def workout_program_exists(self, id_workout_program: int) -> bool:
        return id_workout_program in self.programs

    async def get(self, id_client: int, id_workout_program: int) -> Enrolment | None:
        return next((item for item in self.enrolments
                     if item.id_client == id_client
                     and item.id_workout_program == id_workout_program), None)

    async def create(self, enrolment: Enrolment) -> Enrolment:
        self.enrolments.append(enrolment)
        return enrolment

    async def list_for_client(self, id_client: int) -> list[Enrolment]:
        return [item for item in self.enrolments if item.id_client == id_client]
