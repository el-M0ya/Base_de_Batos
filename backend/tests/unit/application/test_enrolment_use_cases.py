"""Tests for client enrollment application use cases."""

from __future__ import annotations

import unittest
from datetime import date
import pathlib
import sys

from app.application.dto.enrolment_dto import CreateEnrolmentInputDTO
from app.application.exceptions import DuplicateResource, ResourceNotFound
from app.application.use_cases.create_enrolment import CreateEnrolmentUseCase
from app.application.use_cases.list_client_enrolments import ListClientEnrolmentsUseCase
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from fakes.in_memory_enrolment_repository import InMemoryEnrolmentRepository


class EnrolmentUseCaseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = InMemoryEnrolmentRepository(clients={1, 2}, programs={10, 11})
        self.create_use_case = CreateEnrolmentUseCase(self.repository)
        self.list_use_case = ListClientEnrolmentsUseCase(self.repository)

    async def test_creates_enrolment_and_preserves_date(self) -> None:
        requested = date(2026, 3, 14)
        result = await self.create_use_case.execute(
            CreateEnrolmentInputDTO(1, 10, requested)
        )
        self.assertEqual(result.id_client, 1)
        self.assertEqual(result.id_workout_program, 10)
        self.assertEqual(result.enrollment_date, requested)

    async def test_rejects_duplicate_client_program_pair(self) -> None:
        request = CreateEnrolmentInputDTO(1, 10, date(2026, 3, 14))
        await self.create_use_case.execute(request)
        with self.assertRaises(DuplicateResource):
            await self.create_use_case.execute(request)

    async def test_rejects_missing_client(self) -> None:
        with self.assertRaises(ResourceNotFound):
            await self.create_use_case.execute(CreateEnrolmentInputDTO(99, 10))

    async def test_rejects_missing_program(self) -> None:
        with self.assertRaises(ResourceNotFound):
            await self.create_use_case.execute(CreateEnrolmentInputDTO(1, 99))

    async def test_lists_programs_for_client(self) -> None:
        await self.create_use_case.execute(CreateEnrolmentInputDTO(1, 10))
        await self.create_use_case.execute(CreateEnrolmentInputDTO(1, 11))
        await self.create_use_case.execute(CreateEnrolmentInputDTO(2, 11))
        result = await self.list_use_case.execute(1)
        self.assertEqual([item.id_workout_program for item in result], [10, 11])

    async def test_rejects_listing_for_missing_client(self) -> None:
        with self.assertRaises(ResourceNotFound):
            await self.list_use_case.execute(99)


if __name__ == "__main__":
    unittest.main()
