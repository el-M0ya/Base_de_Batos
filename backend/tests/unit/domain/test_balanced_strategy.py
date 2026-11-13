"""Unit tests for the balanced routine-generation strategy (issue E6-01)."""

from __future__ import annotations

import unittest
from decimal import Decimal

from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.routine_structure import BlockType
from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidParameters,
)
from app.domain.strategies.balanced_strategy import BalancedRoutineGenerationStrategy
from app.domain.strategies.routine_generation_strategy import RoutineGenerationRequest
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel

CHEST = MuscleGroup(1, "Chest")
BACK = MuscleGroup(2, "Back")
LEGS = MuscleGroup(3, "Legs")


def build_exercise(
    id_exercise: int,
    name: str,
    exercise_type: ExerciseType,
    muscle_group: MuscleGroup,
    intensity: IntensityLevel = IntensityLevel.MEDIUM,
) -> Exercise:
    return Exercise(
        name=name,
        exercise_type=exercise_type,
        intensity=intensity,
        muscle_group=muscle_group,
        id_trainer_creator=1,
        id_exercise=id_exercise,
    )


def build_request(**overrides: object) -> RoutineGenerationRequest:
    values: dict[str, object] = {
        "candidate_exercises": (
            build_exercise(1, "Bench press", ExerciseType.STRENGTH, CHEST),
            build_exercise(2, "Squat", ExerciseType.STRENGTH, LEGS),
            build_exercise(3, "Deadlift", ExerciseType.STRENGTH, BACK),
            build_exercise(10, "Overhead press", ExerciseType.STRENGTH, CHEST),
            build_exercise(11, "Lunges", ExerciseType.STRENGTH, LEGS),
            build_exercise(4, "Jump rope", ExerciseType.CARDIO, CHEST),
            build_exercise(5, "Running", ExerciseType.CARDIO, LEGS),
            build_exercise(6, "Rowing", ExerciseType.CARDIO, BACK),
            build_exercise(7, "Stretch chest", ExerciseType.FLEXIBILITY, CHEST),
            build_exercise(8, "Stretch back", ExerciseType.FLEXIBILITY, BACK),
            build_exercise(9, "Stretch legs", ExerciseType.FLEXIBILITY, LEGS),
        ),
        "target_intensity": IntensityLevel.MEDIUM,
        "exercise_type_proportions": {
            ExerciseType.STRENGTH: Decimal("0.5"),
            ExerciseType.CARDIO: Decimal("0.3"),
            ExerciseType.FLEXIBILITY: Decimal("0.2"),
        },
        "total_exercises": 10,
        "covered_muscle_groups": (CHEST, BACK, LEGS),
    }
    values.update(overrides)
    return RoutineGenerationRequest(**values)  # type: ignore[arg-type]


class BalancedStrategyProportionTests(unittest.TestCase):
    def test_respects_type_proportions_ca06(self) -> None:
        """CA-06: 0.5 / 0.3 / 0.2 with 10 exercises -> 5 strength, 3 cardio, 2 flexibility."""
        strategy = BalancedRoutineGenerationStrategy()
        result = strategy.generate(build_request())

        counts: dict[ExerciseType, int] = {}
        for item in result.exercises:
            counts[item.exercise.exercise_type] = counts.get(item.exercise.exercise_type, 0) + 1

        self.assertEqual(counts.get(ExerciseType.STRENGTH), 5)
        self.assertEqual(counts.get(ExerciseType.CARDIO), 3)
        self.assertEqual(counts.get(ExerciseType.FLEXIBILITY), 2)
        self.assertEqual(len(result.exercises), 10)

    def test_orders_are_unique_and_positive(self) -> None:
        strategy = BalancedRoutineGenerationStrategy()
        result = strategy.generate(build_request())

        orders = [item.order for item in result.exercises]
        self.assertEqual(orders, list(range(1, len(orders) + 1)))

    def test_blocks_reference_selected_exercises(self) -> None:
        strategy = BalancedRoutineGenerationStrategy()
        result = strategy.generate(build_request())

        self.assertEqual(len(result.block_structure), len(result.exercises))
        self.assertEqual(
            {block.id_exercise for block in result.block_structure},
            {item.exercise.id_exercise for item in result.exercises},
        )
        self.assertTrue(
            all(block.block_type is BlockType.SET for block in result.block_structure)
        )
        self.assertEqual(
            [block.order for block in result.block_structure],
            [item.order for item in result.exercises],
        )

    def test_only_selects_from_covered_muscle_groups(self) -> None:
        strategy = BalancedRoutineGenerationStrategy()
        request = build_request(
            covered_muscle_groups=(LEGS,),
            total_exercises=3,
            exercise_type_proportions={
                ExerciseType.STRENGTH: Decimal("0.5"),
                ExerciseType.CARDIO: Decimal("0.3"),
                ExerciseType.FLEXIBILITY: Decimal("0.2"),
            },
        )
        result = strategy.generate(request)

        self.assertTrue(
            all(item.exercise.muscle_group is LEGS for item in result.exercises)
        )
        self.assertEqual(len(result.exercises), 3)

    def test_raises_when_not_enough_exercises_for_a_type(self) -> None:
        strategy = BalancedRoutineGenerationStrategy()
        # Only 1 cardio exercise available but 3 are required by the proportions.
        request = build_request(
            candidate_exercises=(
                build_exercise(1, "Bench press", ExerciseType.STRENGTH, CHEST),
                build_exercise(2, "Squat", ExerciseType.STRENGTH, LEGS),
                build_exercise(3, "Deadlift", ExerciseType.STRENGTH, BACK),
                build_exercise(10, "Overhead press", ExerciseType.STRENGTH, CHEST),
                build_exercise(11, "Lunges", ExerciseType.STRENGTH, LEGS),
                build_exercise(4, "Jump rope", ExerciseType.CARDIO, CHEST),
                build_exercise(7, "Stretch chest", ExerciseType.FLEXIBILITY, CHEST),
                build_exercise(8, "Stretch back", ExerciseType.FLEXIBILITY, BACK),
            ),
            total_exercises=10,
        )

        with self.assertRaises(InvalidParameters) as context:
            strategy.generate(request)

        self.assertIn(ExerciseType.CARDIO.value, str(context.exception))

    def test_raises_when_total_exercises_is_zero(self) -> None:
        strategy = BalancedRoutineGenerationStrategy()

        with self.assertRaises(InvalidDomainValue):
            build_request(total_exercises=0)

        strategy.generate(build_request(total_exercises=1))


if __name__ == "__main__":
    unittest.main()
