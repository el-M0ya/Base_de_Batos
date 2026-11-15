"""Unit tests for training program management use cases (RF-10, U-2)."""

from __future__ import annotations

import unittest

from app.application.dto.actor import ActorDTO
from app.application.dto.training_program_dto import (
    CreateTrainingProgramInputDTO,
    DeleteTrainingProgramInputDTO,
    SetTrainingProgramMuscleGroupsInputDTO,
    UpdateTrainingProgramInputDTO,
)
from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    PermissionDenied,
    ResourceNotFound,
)
from app.application.services.muscle_group_resolver import MuscleGroupResolver
from app.application.use_cases.create_training_program import (
    CreateTrainingProgramUseCase,
)
from app.application.use_cases.delete_training_program import (
    DeleteTrainingProgramUseCase,
)
from app.application.use_cases.get_training_program import GetTrainingProgramUseCase
from app.application.use_cases.list_training_programs import (
    ListTrainingProgramsUseCase,
)
from app.application.use_cases.set_training_program_muscle_groups import (
    SetTrainingProgramMuscleGroupsUseCase,
)
from app.application.use_cases.update_training_program import (
    UpdateTrainingProgramUseCase,
)
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.workout_program import WorkoutProgram
from app.domain.value_objects.user_role import UserRole
from fakes.in_memory_muscle_group_repository import (
    InMemoryMuscleGroupRepository,
)
from fakes.in_memory_workout_program_repository import (
    InMemoryWorkoutProgramRepository,
)

ADMIN = ActorDTO(id_user=1, role=UserRole.ADMIN)
TRAINER = ActorDTO(id_user=2, role=UserRole.TRAINER)


class TrainingProgramUseCaseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.muscle_groups = InMemoryMuscleGroupRepository(
            [MuscleGroup(1, "Chest"), MuscleGroup(2, "Back")]
        )
        self.programs = InMemoryWorkoutProgramRepository()
        self.resolver = MuscleGroupResolver(self.muscle_groups)
        self.create_use_case = CreateTrainingProgramUseCase(
            self.programs, self.resolver
        )

    async def test_create_persists_program_and_coverage(self) -> None:
        result = await self.create_use_case.execute(
            CreateTrainingProgramInputDTO(
                actor=ADMIN,
                name="  Upper   body ",
                objective="  Build strength ",
                muscle_group_ids=(1, 2),
            )
        )

        self.assertEqual(result.name, "Upper body")
        self.assertEqual(result.objective, "Build strength")
        self.assertEqual(set(result.muscle_group_ids), {1, 2})
        self.assertEqual(
            [group.name for group in result.muscle_groups],
            ["Back", "Chest"],
        )

    async def test_create_rejects_duplicate_name_ignoring_case(self) -> None:
        self.programs = InMemoryWorkoutProgramRepository(
            [WorkoutProgram("Upper body", "Build strength", id_workout_program=1)]
        )
        use_case = CreateTrainingProgramUseCase(self.programs, self.resolver)

        with self.assertRaises(DuplicateResource):
            await use_case.execute(
                CreateTrainingProgramInputDTO(
                    actor=ADMIN,
                    name=" upper BODY",
                    objective="Build strength",
                    muscle_group_ids=(),
                )
            )

    async def test_create_rejects_non_admin_actor(self) -> None:
        with self.assertRaises(PermissionDenied):
            await self.create_use_case.execute(
                CreateTrainingProgramInputDTO(
                    actor=TRAINER,
                    name="Upper body",
                    objective="Build strength",
                    muscle_group_ids=(),
                )
            )

    async def test_create_rejects_missing_muscle_group(self) -> None:
        with self.assertRaises(ResourceNotFound):
            await self.create_use_case.execute(
                CreateTrainingProgramInputDTO(
                    actor=ADMIN,
                    name="Upper body",
                    objective="Build strength",
                    muscle_group_ids=(99,),
                )
            )

    async def test_update_replaces_coverage(self) -> None:
        program = WorkoutProgram(
            "Upper body",
            "Build strength",
            id_workout_program=1,
            target_muscle_groups=[MuscleGroup(1, "Chest")],
        )
        self.programs = InMemoryWorkoutProgramRepository([program])
        use_case = UpdateTrainingProgramUseCase(self.programs, self.resolver)

        result = await use_case.execute(
            UpdateTrainingProgramInputDTO(
                actor=ADMIN,
                id_workout_program=1,
                name="Upper body",
                objective="Build strength",
                muscle_group_ids=(2,),
            )
        )

        self.assertEqual(result.muscle_group_ids, (2,))
        self.assertEqual([group.name for group in result.muscle_groups], ["Back"])

    async def test_update_rejects_duplicate_name_of_another_program(self) -> None:
        self.programs = InMemoryWorkoutProgramRepository(
            [
                WorkoutProgram("Upper body", "Build strength", id_workout_program=1),
                WorkoutProgram("Lower body", "Build legs", id_workout_program=2),
            ]
        )
        use_case = UpdateTrainingProgramUseCase(self.programs, self.resolver)

        with self.assertRaises(DuplicateResource):
            await use_case.execute(
                UpdateTrainingProgramInputDTO(
                    actor=ADMIN,
                    id_workout_program=1,
                    name="LOWER BODY",
                    objective="Build strength",
                    muscle_group_ids=(),
                )
            )

    async def test_set_coverage_replaces_associations(self) -> None:
        program = WorkoutProgram(
            "Upper body",
            "Build strength",
            id_workout_program=1,
            target_muscle_groups=[MuscleGroup(1, "Chest")],
        )
        self.programs = InMemoryWorkoutProgramRepository([program])
        use_case = SetTrainingProgramMuscleGroupsUseCase(
            self.programs, self.resolver
        )

        result = await use_case.execute(
            SetTrainingProgramMuscleGroupsInputDTO(
                actor=ADMIN,
                id_workout_program=1,
                muscle_group_ids=(2, 1),
            )
        )

        self.assertEqual(set(result.muscle_group_ids), {1, 2})

    async def test_delete_removes_program(self) -> None:
        self.programs = InMemoryWorkoutProgramRepository(
            [WorkoutProgram("Upper body", "Build strength", id_workout_program=1)]
        )
        use_case = DeleteTrainingProgramUseCase(self.programs)

        await use_case.execute(
            DeleteTrainingProgramInputDTO(actor=ADMIN, id_workout_program=1)
        )

        self.assertIsNone(await self.programs.get_by_id(1))

    async def test_delete_translates_integrity_failure(self) -> None:
        program = WorkoutProgram("Upper body", "Build strength", id_workout_program=1)
        self.programs = InMemoryWorkoutProgramRepository([program])
        self.programs.blocked_deletion_ids.add(1)
        use_case = DeleteTrainingProgramUseCase(self.programs)

        with self.assertRaises(BusinessRuleViolation):
            await use_case.execute(
                DeleteTrainingProgramInputDTO(actor=ADMIN, id_workout_program=1)
            )

    async def test_get_and_list_return_programs_with_coverage(self) -> None:
        program = WorkoutProgram(
            "Upper body",
            "Build strength",
            id_workout_program=1,
            target_muscle_groups=[MuscleGroup(1, "Chest")],
        )
        self.programs = InMemoryWorkoutProgramRepository([program])
        get_use_case = GetTrainingProgramUseCase(self.programs)
        list_use_case = ListTrainingProgramsUseCase(self.programs)

        result = await get_use_case.execute(1)
        every_program = await list_use_case.execute()

        self.assertEqual(result.name, "Upper body")
        self.assertEqual(result.muscle_group_ids, (1,))
        self.assertEqual([item.name for item in every_program], ["Upper body"])

    async def test_get_rejects_missing_program(self) -> None:
        with self.assertRaises(ResourceNotFound):
            await GetTrainingProgramUseCase(self.programs).execute(99)


if __name__ == "__main__":
    unittest.main()
