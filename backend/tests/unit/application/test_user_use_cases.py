"""Unit tests for administrator-managed user accounts."""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from fakes.in_memory_user_repository import InMemoryUserRepository

from app.application.dto.actor import ActorDTO
from app.application.dto.user_dto import (
    ClientProfileInputDTO,
    CreateUserInputDTO,
    TrainerProfileInputDTO,
    UpdateUserInputDTO,
)
from app.application.exceptions import (
    DuplicateResource,
    PermissionDenied,
    ResourceNotFound,
)
from app.application.use_cases.user.create_user import CreateUserUseCase
from app.application.use_cases.user.deactivate_user import DeactivateUserUseCase
from app.application.use_cases.user.list_users import ListUsersUseCase
from app.application.use_cases.user.update_user import UpdateUserUseCase


class UserUseCaseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = InMemoryUserRepository()
        self.create = CreateUserUseCase(self.repository)
        self.list = ListUsersUseCase(self.repository)
        self.update = UpdateUserUseCase(self.repository)
        self.deactivate = DeactivateUserUseCase(self.repository)
        self.admin = ActorDTO(1, "ADMIN")
        self.trainer = ActorDTO(2, "TRAINER")
        self.client = ActorDTO(3, "CLIENT")

    async def test_admin_creates_trainer_with_profile(self) -> None:
        output = await self.create.execute(
            CreateUserInputDTO(
                actor=self.admin,
                name="Trainer",
                email="trainer@example.com",
                password_hash="hash",
                role="TRAINER",
                trainer=TrainerProfileInputDTO("CARDIO"),
            )
        )

        self.assertEqual(output.role, "TRAINER")
        self.assertEqual(output.trainer.specialty, "CARDIO")
        self.assertIsNone(output.client)

    async def test_admin_creates_client_with_profile(self) -> None:
        output = await self.create.execute(
            CreateUserInputDTO(
                actor=self.admin,
                name="Client",
                email="client@example.com",
                password_hash="hash",
                role="CLIENT",
                client=ClientProfileInputDTO(age=25, id_site=4),
            )
        )

        self.assertEqual(output.client.age, 25)
        self.assertEqual(output.client.id_site, 4)

    async def test_non_admin_cannot_manage_users(self) -> None:
        with self.assertRaises(PermissionDenied):
            await self.create.execute(
                CreateUserInputDTO(
                    actor=self.trainer,
                    name="User",
                    email="user@example.com",
                    password_hash="hash",
                    role="ADMIN",
                )
            )

    async def test_duplicate_email_is_rejected(self) -> None:
        await self.create.execute(
            CreateUserInputDTO(
                actor=self.admin,
                name="First",
                email="same@example.com",
                password_hash="hash",
                role="ADMIN",
            )
        )

        with self.assertRaises(DuplicateResource):
            await self.create.execute(
                CreateUserInputDTO(
                    actor=self.admin,
                    name="Second",
                    email="same@example.com",
                    password_hash="hash",
                    role="ADMIN",
                )
            )

    async def test_list_returns_profiles(self) -> None:
        await self.create.execute(
            CreateUserInputDTO(
                actor=self.admin,
                name="Client",
                email="client@example.com",
                password_hash="hash",
                role="CLIENT",
                client=ClientProfileInputDTO(age=30, id_site=2),
            )
        )

        output = await self.list.execute(self.admin)

        self.assertEqual(len(output), 1)
        self.assertEqual(output[0].client.id_site, 2)

    async def test_update_preserves_profile_when_profile_is_omitted(self) -> None:
        created = await self.create.execute(
            CreateUserInputDTO(
                actor=self.admin,
                name="Client",
                email="client@example.com",
                password_hash="hash",
                role="CLIENT",
                client=ClientProfileInputDTO(age=30, id_site=2),
            )
        )

        output = await self.update.execute(
            UpdateUserInputDTO(
                actor=self.admin,
                id_user=created.id_user,
                name="Updated Client",
            )
        )

        self.assertEqual(output.name, "Updated Client")
        self.assertEqual(output.client.id_site, 2)

    async def test_deactivation_preserves_account_and_profile(self) -> None:
        created = await self.create.execute(
            CreateUserInputDTO(
                actor=self.admin,
                name="Client",
                email="client@example.com",
                password_hash="hash",
                role="CLIENT",
                client=ClientProfileInputDTO(age=30, id_site=2),
            )
        )

        output = await self.deactivate.execute(
            UpdateUserInputDTO(actor=self.admin, id_user=created.id_user)
        )

        self.assertFalse(output.active)
        self.assertIsNotNone(output.client)
        self.assertIsNotNone(await self.repository.get_by_id(created.id_user))

    async def test_update_missing_user_is_rejected(self) -> None:
        with self.assertRaises(ResourceNotFound):
            await self.update.execute(
                UpdateUserInputDTO(actor=self.admin, id_user=999, name="Missing")
            )


if __name__ == "__main__":
    unittest.main()
