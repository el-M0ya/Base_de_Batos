"""Tests for requesting a linked successor after routine review."""

from __future__ import annotations

import pathlib
import sys
import unittest
from datetime import date
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from fakes.in_memory_authorisation_repository import InMemoryAuthorisationRepository
from fakes.in_memory_exercise_repository import InMemoryExerciseRepository
from fakes.in_memory_routine_repository import InMemoryRoutineRepository
from fakes.in_memory_workout_program_repository import InMemoryWorkoutProgramRepository

from app.application.dto.actor import ActorDTO
from app.application.dto.routine_replacement_dto import ReplaceRoutineInputDTO
from app.application.exceptions import BusinessRuleViolation, PermissionDenied
from app.application.use_cases.generate_routine import GenerateRoutineUseCase
from app.application.use_cases.replace_routine import ReplaceRoutineUseCase
from app.domain.entities.authorisation import Authorisation
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.routine import Routine, RoutineStatus
from app.domain.entities.routine_structure import RoutineStructure
from app.domain.entities.routine_validation import RoutineValidation, ValidationDecision
from app.domain.entities.workout_program import WorkoutProgram
from app.domain.strategies.balanced_strategy import BalancedRoutineGenerationStrategy
from app.domain.strategies.strategy_registry import StrategyRegistry
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.domain.value_objects.user_role import UserRole


TODAY = date(2026, 5, 1)
PROGRAM_ID = 10
SOURCE_ID = 1
TRAINER_ID = 7
ROOM_CHIEF_ID = 8
CHEST = MuscleGroup(id_muscle_group=1, name="Chest")


def _fixture(*, with_review: bool = True, generation_authorised: bool = True):
    source = Routine(
        id_routine=SOURCE_ID,
        id_workout_program=PROGRAM_ID,
        id_trainer_creator=TRAINER_ID,
        status=RoutineStatus.REJECTED,
        creation_date=date(2026, 4, 1),
    )
    routines = InMemoryRoutineRepository(
        [(source, RoutineStructure(id_routine=SOURCE_ID))]
    )
    review = RoutineValidation(
        id_routine=SOURCE_ID,
        id_room_chief=ROOM_CHIEF_ID,
        decision=ValidationDecision.REJECTED,
        validation_date=date(2026, 4, 2),
        observations="Reduce the volume.",
    )
    if with_review:
        routines.validations[SOURCE_ID] = [review]

    program = WorkoutProgram(
        id_workout_program=PROGRAM_ID,
        name="Strength Base",
        objective="General strength",
        target_muscle_groups=[CHEST],
    )
    programs = InMemoryWorkoutProgramRepository([program])
    programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = Authorisation(
        id_trainer=TRAINER_ID,
        id_workout_program=PROGRAM_ID,
        can_generate=generation_authorised,
        can_validate=not generation_authorised,
        start_date=date(2026, 1, 1),
    )
    exercises = InMemoryExerciseRepository(
        [Exercise(
            id_exercise=1,
            name="Bench press",
            exercise_type=ExerciseType.STRENGTH,
            intensity=IntensityLevel.HIGH,
            muscle_group=CHEST,
            id_trainer_creator=TRAINER_ID,
        )]
    )
    authorisations = InMemoryAuthorisationRepository([
        Authorisation(
            id_trainer=ROOM_CHIEF_ID,
            id_workout_program=PROGRAM_ID,
            can_validate=True,
            start_date=date(2026, 1, 1),
        )
    ])
    generator = GenerateRoutineUseCase(
        programs,
        exercises,
        routines,
        StrategyRegistry([BalancedRoutineGenerationStrategy()]),
    )
    use_case = ReplaceRoutineUseCase(routines, authorisations, generator)
    request = ReplaceRoutineInputDTO(
        actor=ActorDTO(id_user=ROOM_CHIEF_ID, role=UserRole.TRAINER),
        id_routine=SOURCE_ID,
        strategy_name="balanced",
        total_exercises=1,
        target_intensity=IntensityLevel.HIGH,
        exercise_type_proportions={ExerciseType.STRENGTH: Decimal("1")},
        request_date=TODAY,
    )
    return use_case, routines, request, review


class ReplaceRoutineUseCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_authorised_room_chief_generates_linked_successor(self) -> None:
        use_case, routines, request, original_review = _fixture()

        result = await use_case.execute(request)

        self.assertEqual(result.replaced_routine.status, RoutineStatus.REPLACED)
        successor = result.generated_successor.routine
        self.assertEqual(successor.id_routine_origin, SOURCE_ID)
        self.assertEqual(successor.id_trainer_creator, TRAINER_ID)
        self.assertEqual(successor.status, RoutineStatus.DRAFT)
        self.assertEqual(routines.validations[SOURCE_ID], [original_review])
        self.assertEqual(len(routines.saved), 1)

    async def test_room_chief_without_validation_grant_is_denied(self) -> None:
        use_case, routines, request, _ = _fixture()
        use_case._authorisations = InMemoryAuthorisationRepository()

        with self.assertRaises(PermissionDenied):
            await use_case.execute(request)

        self.assertEqual(routines.routines[SOURCE_ID].status, RoutineStatus.REJECTED)
        self.assertEqual(routines.saved, [])

    async def test_routine_without_review_cannot_be_replaced(self) -> None:
        use_case, routines, request, _ = _fixture(with_review=False)

        with self.assertRaises(BusinessRuleViolation):
            await use_case.execute(request)

        self.assertEqual(routines.routines[SOURCE_ID].status, RoutineStatus.REJECTED)
        self.assertEqual(routines.saved, [])

    async def test_generation_failure_does_not_mark_source_replaced(self) -> None:
        use_case, routines, request, _ = _fixture(generation_authorised=False)

        with self.assertRaises(PermissionDenied):
            await use_case.execute(request)

        self.assertEqual(routines.routines[SOURCE_ID].status, RoutineStatus.REJECTED)
        self.assertEqual(routines.saved, [])

    async def test_source_update_failure_is_reported(self) -> None:
        use_case, routines, request, _ = _fixture()
        routines.fail_on_mark_replaced = True

        with self.assertRaises(BusinessRuleViolation):
            await use_case.execute(request)

        self.assertEqual(routines.routines[SOURCE_ID].status, RoutineStatus.REJECTED)


if __name__ == "__main__":
    unittest.main()
