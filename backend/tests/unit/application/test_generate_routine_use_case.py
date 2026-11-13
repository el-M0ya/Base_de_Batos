"""Unit tests for the routine-generation use case (issue E6-02).

The tests use only in-memory repositories and the application/domain layers.
They verify validation, strategy selection, aggregate construction, and the
persistence hand-off without importing FastAPI or psycopg.
"""

from __future__ import annotations

import pathlib
import sys
import unittest
from datetime import date
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from fakes.in_memory_exercise_repository import InMemoryExerciseRepository
from fakes.in_memory_routine_repository import InMemoryRoutineRepository
from fakes.in_memory_workout_program_repository import (
    InMemoryWorkoutProgramRepository,
)

from app.application.dto.actor import ActorDTO
from app.application.dto.routine_generation_dto import GenerateRoutineInputDTO
from app.application.exceptions import (
    BusinessRuleViolation,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.application.use_cases.generate_routine import GenerateRoutineUseCase
from app.domain.entities.authorisation import Authorisation
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.routine import RoutineStatus
from app.domain.entities.routine_structure import BlockType, RoutineBlock
from app.domain.entities.workout_program import WorkoutProgram
from app.domain.strategies.balanced_strategy import BalancedRoutineGenerationStrategy
from app.domain.strategies.routine_generation_strategy import (
    GeneratedExercise,
    RoutineGenerationRequest,
    RoutineGenerationResult,
    RoutineGenerationStrategy,
)
from app.domain.strategies.strategy_registry import StrategyRegistry
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel
from app.domain.value_objects.user_role import UserRole


TRAINER_ID = 7
PROGRAM_ID = 10
GENERATION_DATE = date(2026, 5, 1)

CHEST = MuscleGroup(id_muscle_group=1, name="Chest")
LEGS = MuscleGroup(id_muscle_group=2, name="Legs")


def _exercise(
    identifier: int,
    name: str,
    exercise_type: ExerciseType,
    muscle_group: MuscleGroup = CHEST,
    intensity: IntensityLevel = IntensityLevel.HIGH,
) -> Exercise:
    """Build a persisted exercise for the in-memory bank."""
    return Exercise(
        id_exercise=identifier,
        name=name,
        exercise_type=exercise_type,
        intensity=intensity,
        muscle_group=muscle_group,
        id_trainer_creator=TRAINER_ID,
    )


def _program(*groups: MuscleGroup) -> WorkoutProgram:
    """Build a persisted program with the supplied coverage."""
    return WorkoutProgram(
        id_workout_program=PROGRAM_ID,
        name="Strength Base",
        objective="General strength",
        target_muscle_groups=list(groups),
    )


def _authorisation(
    *,
    can_generate: bool = True,
    start_date: date = date(2026, 1, 1),
    end_date: date | None = None,
) -> Authorisation:
    """Build an authorisation that is valid for the normal test date."""
    return Authorisation(
        id_trainer=TRAINER_ID,
        id_workout_program=PROGRAM_ID,
        can_generate=can_generate,
        can_validate=not can_generate,
        start_date=start_date,
        end_date=end_date,
    )


def _input_dto(
    *,
    actor: ActorDTO | None = None,
    total_exercises: int = 4,
    proportions: dict[ExerciseType, Decimal] | None = None,
    strategy_name: str = "balanced",
) -> GenerateRoutineInputDTO:
    """Build a valid request unless a test overrides one criterion."""
    return GenerateRoutineInputDTO(
        actor=actor or ActorDTO(id_user=TRAINER_ID, role=UserRole.TRAINER),
        id_workout_program=PROGRAM_ID,
        strategy_name=strategy_name,
        total_exercises=total_exercises,
        target_intensity=IntensityLevel.HIGH,
        exercise_type_proportions=proportions
        or {
            ExerciseType.STRENGTH: Decimal("0.5"),
            ExerciseType.CARDIO: Decimal("0.5"),
        },
        generation_date=GENERATION_DATE,
    )


class RecordingStrategy(RoutineGenerationStrategy):
    """Minimal strategy used to prove registry selection."""

    def __init__(self) -> None:
        self.requests: list[RoutineGenerationRequest] = []

    @property
    def name(self) -> str:
        return "recording"

    def generate(
        self, request: RoutineGenerationRequest
    ) -> RoutineGenerationResult:
        self.requests.append(request)
        exercise = request.candidate_exercises[0]
        return RoutineGenerationResult(
            exercises=(
                GeneratedExercise(
                    exercise=exercise,
                    order=1,
                    sets=3,
                    repetitions=10,
                    rest_seconds=60,
                ),
            ),
            block_structure=(
                RoutineBlock(
                    block_type=BlockType.SET,
                    order=1,
                    id_exercise=exercise.id_exercise,
                    sets=3,
                    repetitions=10,
                    rest_seconds=60,
                ),
            ),
        )


class GenerateRoutineUseCaseTests(unittest.IsolatedAsyncioTestCase):
    """Behavioural tests for the generation use case."""

    def _collaborators(
        self,
        *,
        program_repository: InMemoryWorkoutProgramRepository | None = None,
        exercise_repository: InMemoryExerciseRepository | None = None,
        routine_repository: InMemoryRoutineRepository | None = None,
        strategy_registry: StrategyRegistry | None = None,
    ) -> tuple[
        GenerateRoutineUseCase,
        InMemoryWorkoutProgramRepository,
        InMemoryExerciseRepository,
        InMemoryRoutineRepository,
    ]:
        """Build the use case and expose the fakes for assertions."""
        programs = program_repository or InMemoryWorkoutProgramRepository(
            [_program(CHEST)]
        )
        exercises = exercise_repository or InMemoryExerciseRepository()
        routines = routine_repository or InMemoryRoutineRepository()
        strategies = strategy_registry or StrategyRegistry(
            [BalancedRoutineGenerationStrategy()]
        )
        return (
            GenerateRoutineUseCase(programs, exercises, routines, strategies),
            programs,
            exercises,
            routines,
        )

    def _seeded_exercises(self) -> InMemoryExerciseRepository:
        """Return a bank with enough covered and uncovered exercises."""
        return InMemoryExerciseRepository(
            [
                _exercise(101, "Bench Press", ExerciseType.STRENGTH),
                _exercise(102, "Push Up", ExerciseType.STRENGTH),
                _exercise(201, "Jump Rope", ExerciseType.CARDIO),
                _exercise(202, "Rowing", ExerciseType.CARDIO),
                _exercise(301, "Chest Stretch", ExerciseType.FLEXIBILITY),
                _exercise(
                    401,
                    "Back Squat",
                    ExerciseType.STRENGTH,
                    muscle_group=LEGS,
                ),
            ]
        )

    async def test_generates_complete_routine_and_persists_aggregate(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation()
        use_case, _, _, routines = self._collaborators(
            program_repository=programs,
            exercise_repository=self._seeded_exercises(),
        )

        result = await use_case.execute(_input_dto())

        self.assertEqual(result.routine.id_routine, 1)
        self.assertEqual(result.routine.status, RoutineStatus.DRAFT)
        self.assertEqual(result.routine.id_workout_program, PROGRAM_ID)
        self.assertEqual(result.routine.id_trainer_creator, TRAINER_ID)
        self.assertEqual(result.routine.creation_date, GENERATION_DATE)

        self.assertEqual(result.parameters.id_routine, 1)
        self.assertEqual(result.parameters.total_exercises, 4)
        self.assertEqual(result.parameters.intensity_level.value, "HIGH")
        self.assertEqual(result.parameters.cardio_ratio, Decimal("50.00"))
        self.assertEqual(result.parameters.strength_ratio, Decimal("50.00"))
        self.assertEqual(result.parameters.flexibility_ratio, Decimal("0.00"))
        self.assertEqual(result.parameters.covered_muscle_group_ids, [1])

        self.assertEqual(len(result.composition), 4)
        types = [item.exercise.exercise_type for item in result.composition]
        self.assertEqual(types.count(ExerciseType.STRENGTH), 2)
        self.assertEqual(types.count(ExerciseType.CARDIO), 2)
        self.assertNotIn(
            401,
            {item.exercise.id_exercise for item in result.composition},
        )

        self.assertEqual(result.structure.id_routine, 1)
        self.assertEqual(len(result.structure.blocks), 4)
        self.assertTrue(
            all(block.block_type is BlockType.SET for block in result.structure.blocks)
        )
        self.assertEqual(
            {block.id_exercise for block in result.structure.blocks},
            {item.exercise.id_exercise for item in result.composition},
        )

        self.assertEqual(len(routines.saved), 1)
        saved_routine, saved_structure = routines.saved[0]
        self.assertIs(saved_routine, result.routine)
        self.assertIs(saved_structure, result.structure)
        self.assertEqual(
            getattr(saved_routine, "_parameters").covered_muscle_group_ids,
            [1],
        )
        self.assertEqual(len(getattr(saved_routine, "_contains")), 4)

    async def test_uses_requested_strategy_through_registry(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation()
        recording = RecordingStrategy()
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=InMemoryExerciseRepository(
                [_exercise(101, "Bench Press", ExerciseType.STRENGTH)]
            ),
            strategy_registry=StrategyRegistry([recording]),
        )

        result = await use_case.execute(
            _input_dto(
                total_exercises=1,
                proportions={ExerciseType.STRENGTH: Decimal("1")},
                strategy_name="recording",
            )
        )

        self.assertEqual(len(recording.requests), 1)
        self.assertEqual(len(result.composition), 1)
        self.assertEqual(result.composition[0].exercise.id_exercise, 101)

    async def test_rejects_non_trainer_actor(self) -> None:
        use_case, _, _, _ = self._collaborators(
            exercise_repository=self._seeded_exercises()
        )
        actor = ActorDTO(id_user=99, role=UserRole.CLIENT)

        with self.assertRaises(PermissionDenied):
            await use_case.execute(_input_dto(actor=actor))

    async def test_rejects_missing_program(self) -> None:
        use_case, _, _, _ = self._collaborators(
            program_repository=InMemoryWorkoutProgramRepository(),
            exercise_repository=self._seeded_exercises(),
        )

        with self.assertRaises(ResourceNotFound):
            await use_case.execute(_input_dto())

    async def test_rejects_missing_authorisation(self) -> None:
        use_case, _, _, _ = self._collaborators(
            exercise_repository=self._seeded_exercises()
        )

        with self.assertRaises(PermissionDenied):
            await use_case.execute(_input_dto())

    async def test_rejects_expired_authorisation(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=self._seeded_exercises(),
        )

        with self.assertRaises(PermissionDenied):
            await use_case.execute(_input_dto())

    async def test_rejects_authorisation_without_generation_permission(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation(
            can_generate=False
        )
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=self._seeded_exercises(),
        )

        with self.assertRaises(PermissionDenied):
            await use_case.execute(_input_dto())

    async def test_rejects_non_positive_total(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation()
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=self._seeded_exercises(),
        )

        with self.assertRaises(InvalidInput):
            await use_case.execute(_input_dto(total_exercises=0))

    async def test_rejects_proportions_that_do_not_sum_to_one(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation()
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=self._seeded_exercises(),
        )

        with self.assertRaises(InvalidInput):
            await use_case.execute(
                _input_dto(
                    proportions={
                        ExerciseType.STRENGTH: Decimal("0.6"),
                        ExerciseType.CARDIO: Decimal("0.6"),
                    }
                )
            )

    async def test_rejects_proportions_outside_unit_interval(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation()
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=self._seeded_exercises(),
        )

        with self.assertRaises(InvalidInput):
            await use_case.execute(
                _input_dto(
                    proportions={ExerciseType.STRENGTH: Decimal("1.1")}
                )
            )

    async def test_rejects_unknown_strategy(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation()
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=self._seeded_exercises(),
        )

        with self.assertRaises(InvalidInput):
            await use_case.execute(_input_dto(strategy_name="missing"))

    async def test_rejects_insufficient_candidates_for_proportions(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation()
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=InMemoryExerciseRepository(
                [
                    _exercise(101, "Bench Press", ExerciseType.STRENGTH),
                    _exercise(102, "Push Up", ExerciseType.STRENGTH),
                ]
            ),
        )

        with self.assertRaises(InvalidInput):
            await use_case.execute(
                _input_dto(
                    proportions={
                        ExerciseType.STRENGTH: Decimal("0.5"),
                        ExerciseType.CARDIO: Decimal("0.5"),
                    }
                )
            )

    async def test_rejects_program_without_coverage(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program()])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation()
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=self._seeded_exercises(),
        )

        with self.assertRaises(BusinessRuleViolation):
            await use_case.execute(_input_dto())

    async def test_rejects_when_no_candidates_exist(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation()
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=InMemoryExerciseRepository(),
        )

        with self.assertRaises(BusinessRuleViolation):
            await use_case.execute(_input_dto())

    async def test_propagates_persistence_failure_without_saving(self) -> None:
        programs = InMemoryWorkoutProgramRepository([_program(CHEST)])
        programs.authorisations[(TRAINER_ID, PROGRAM_ID)] = _authorisation()
        routines = InMemoryRoutineRepository()
        routines.fail_on_save = True
        use_case, _, _, _ = self._collaborators(
            program_repository=programs,
            exercise_repository=self._seeded_exercises(),
            routine_repository=routines,
        )

        with self.assertRaises(BusinessRuleViolation):
            await use_case.execute(_input_dto())
        self.assertEqual(routines.saved, [])


if __name__ == "__main__":
    unittest.main()
