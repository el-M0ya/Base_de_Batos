"""Persistence contract for client enrollments in workout programs."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.enrolment import Enrolment


class EnrolmentRepository(ABC):
    @abstractmethod
    async def client_exists(self, id_client: int) -> bool:
        """Return whether a client profile exists."""

    @abstractmethod
    async def workout_program_exists(self, id_workout_program: int) -> bool:
        """Return whether a workout program exists."""

    @abstractmethod
    async def get(self, id_client: int, id_workout_program: int) -> Enrolment | None:
        """Return an enrollment for a client/program pair."""

    @abstractmethod
    async def create(self, enrolment: Enrolment) -> Enrolment:
        """Persist and return an enrollment."""

    @abstractmethod
    async def list_for_client(self, id_client: int) -> list[Enrolment]:
        """Return all programs in which the client is enrolled."""
