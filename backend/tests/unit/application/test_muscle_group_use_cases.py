"""Unit tests for muscle group catalog use cases (U-3)."""

from __future__ import annotations

import unittest

from app.application.dto.actor import ActorDTO
from app.application.dto.muscle_group_dto import (
    CreateMuscleGroupInputDTO,
    DeleteMuscleGroupInputDTO,
    UpdateMuscleGroupInputDTO,
)
from app.application.exceptions import (
    DuplicateResource,
    PermissionDenied,
    ResourceNotFound,
)
from app.application.use_cases.create_muscle_group import CreateMuscleGroupUseCase
from app.application.use_cases.delete_muscle_group import DeleteMuscleGroupUseCase
from app.application.use_cases.get_muscle_group import GetMuscleGroupUseCase
from app.application.use_cases.list_muscle_groups import ListMuscleGroupsUseCase
from app.application.use_cases.update_muscle_group import UpdateMuscleGroupUseCase
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.value_objects.user_role import UserRole
from fakes.in_memory_muscle_group_repository import (
    InMemoryMuscleGroupRepository,
)

ADMIN = ActorDTO(id_user=1, role=UserRole.ADMIN)
TRAINER = ActorDTO(id_user=2, role=UserRole.TRAINER)


class MuscleGroupUseCaseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = InMemoryMuscleGroupRepository(
            [MuscleGroup(1, "Chest")]
        )

    async def test_create_persists_normalized_name(self) -> None:
        use_case = CreateMuscleGroupUseCase(self.repository)

        result = await use_case.execute(
            CreateMuscleGroupInputDTO(actor=ADMIN, name="  Lower   body ")
        )

        self.assertEqual(result.name, "Lower body")
        self.assertIsNotNone(result.id_muscle_group)
        self.assertIsNotNone(await self.repository.get_by_id(result.id_muscle_group))

    async def test_create_rejects_duplicate_name_ignoring_case(self) -> None:
        use_case = CreateMuscleGroupUseCase(self.repository)

        with self.assertRaises(DuplicateResource):
            await use_case.execute(
                CreateMuscleGroupInputDTO(actor=ADMIN, name="  chest ")
            )

    async def test_create_rejects_non_admin_actor(self) -> None:
        use_case = CreateMuscleGroupUseCase(self.repository)

        with self.assertRaises(PermissionDenied):
            await use_case.execute(
                CreateMuscleGroupInputDTO(actor=TRAINER, name="Legs")
            )

    async def test_update_renames_existing_group(self) -> None:
        use_case = UpdateMuscleGroupUseCase(self.repository)

        result = await use_case.execute(
            UpdateMuscleGroupInputDTO(
                actor=ADMIN,
                id_muscle_group=1,
                name="Pectoral",
            )
        )

        self.assertEqual(result.name, "Pectoral")

    async def test_update_rejects_duplicate_name_of_another_group(self) -> None:
        self.repository = InMemoryMuscleGroupRepository(
            [MuscleGroup(1, "Chest"), MuscleGroup(2, "Back")]
        )
        use_case = UpdateMuscleGroupUseCase(self.repository)

        with self.assertRaises(DuplicateResource):
            await use_case.execute(
                UpdateMuscleGroupInputDTO(
                    actor=ADMIN,
                    id_muscle_group=1,
                    name="back",
                )
            )

    async def test_update_rejects_missing_group(self) -> None:
        use_case = UpdateMuscleGroupUseCase(self.repository)

        with self.assertRaises(ResourceNotFound):
            await use_case.execute(
                UpdateMuscleGroupInputDTO(
                    actor=ADMIN,
                    id_muscle_group=99,
                    name="Legs",
                )
            )

    async def test_delete_removes_group(self) -> None:
        use_case = DeleteMuscleGroupUseCase(self.repository)

        await use_case.execute(
            DeleteMuscleGroupInputDTO(actor=ADMIN, id_muscle_group=1)
        )

        self.assertIsNone(await self.repository.get_by_id(1))

    async def test_delete_rejects_missing_group(self) -> None:
        use_case = DeleteMuscleGroupUseCase(self.repository)

        with self.assertRaises(ResourceNotFound):
            await use_case.execute(
                DeleteMuscleGroupInputDTO(actor=ADMIN, id_muscle_group=99)
            )

    async def test_get_and_list_return_catalog_entries(self) -> None:
        get_use_case = GetMuscleGroupUseCase(self.repository)
        list_use_case = ListMuscleGroupsUseCase(self.repository)

        result = await get_use_case.execute(1)
        every_group = await list_use_case.execute()

        self.assertEqual(result.name, "Chest")
        self.assertEqual([group.name for group in every_group], ["Chest"])


if __name__ == "__main__":
    unittest.main()
