"""Unit tests for the routine-generation Strategy pattern."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest
from decimal import Decimal

from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.routine_structure import BlockType
from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    InvalidParameters,
    UnknownGenerationStrategy,
)
from app.domain.strategies import (
    GeneratedExercise,
    RoutineGenerationRequest,
    RoutineGenerationResult,
    StrategyRegistry,
)
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel

# The application tests also import a top-level ``fakes`` package. Loading this
# module by path avoids a ``sys.modules`` collision in the full test suite.
_FAKE_STRATEGIES_PATH = (
    pathlib.Path(__file__).resolve().parent / "fakes" / "fake_strategies.py"
)
_FAKE_STRATEGIES_SPEC = importlib.util.spec_from_file_location(
    "domain_fake_strategies", _FAKE_STRATEGIES_PATH
)
if _FAKE_STRATEGIES_SPEC is None or _FAKE_STRATEGIES_SPEC.loader is None:
    raise ImportError(f"Cannot load fake strategies from {_FAKE_STRATEGIES_PATH}")
_FAKE_STRATEGIES_MODULE = importlib.util.module_from_spec(_FAKE_STRATEGIES_SPEC)
sys.modules[_FAKE_STRATEGIES_SPEC.name] = _FAKE_STRATEGIES_MODULE
_FAKE_STRATEGIES_SPEC.loader.exec_module(_FAKE_STRATEGIES_MODULE)

CardioFirstFakeStrategy = _FAKE_STRATEGIES_MODULE.CardioFirstFakeStrategy
StrengthFirstFakeStrategy = _FAKE_STRATEGIES_MODULE.StrengthFirstFakeStrategy

CHEST = MuscleGroup(1, "Chest")
BACK = MuscleGroup(2, "Back")
LEGS = MuscleGroup(3, "Legs")


def build_exercise(
    id_exercise: int,
    name: str,
    exercise_type: ExerciseType,
    muscle_group: MuscleGroup,
) -> Exercise:
    return Exercise(
        name=name,
        exercise_type=exercise_type,
        intensity=IntensityLevel.MEDIUM,
        muscle_group=muscle_group,
        id_trainer_creator=1,
        id_exercise=id_exercise,
    )


STRENGTH_CHEST = build_exercise(1, "Bench press", ExerciseType.STRENGTH, CHEST)
CARDIO_CHEST = build_exercise(2, "Jump rope", ExerciseType.CARDIO, CHEST)
STRENGTH_BACK = build_exercise(3, "Pull-up", ExerciseType.STRENGTH, BACK)
FLEXIBILITY_LEGS = build_exercise(
    4, "Hip opener", ExerciseType.FLEXIBILITY, LEGS
)


def build_request(**overrides: object) -> RoutineGenerationRequest:
    values: dict[str, object] = {
        "candidate_exercises": (
            STRENGTH_CHEST,
            CARDIO_CHEST,
            STRENGTH_BACK,
            FLEXIBILITY_LEGS,
        ),
        "target_intensity": IntensityLevel.MEDIUM,
        "exercise_type_proportions": {
            ExerciseType.STRENGTH: Decimal("0.5"),
            ExerciseType.CARDIO: Decimal("0.25"),
            ExerciseType.FLEXIBILITY: Decimal("0.25"),
        },
        "total_exercises": 2,
        "covered_muscle_groups": (CHEST, BACK),
    }
    values.update(overrides)
    return RoutineGenerationRequest(**values)  # type: ignore[arg-type]


class RoutineGenerationRequestTests(unittest.TestCase):
    def test_request_normalises_value_objects(self) -> None:
        request = build_request(
            target_intensity="medio",
            exercise_type_proportions={"strength": "0.5", "cardio": 0.5},
        )

        self.assertIs(request.target_intensity, IntensityLevel.MEDIUM)
        self.assertEqual(
            request.exercise_type_proportions,
            {
                ExerciseType.STRENGTH: Decimal("0.5"),
                ExerciseType.CARDIO: Decimal("0.5"),
            },
        )
        self.assertIsInstance(request.candidate_exercises, tuple)
        self.assertIsInstance(request.covered_muscle_groups, tuple)

    def test_request_rejects_proportions_that_do_not_sum_to_one(self) -> None:
        with self.assertRaises(InvalidParameters):
            build_request(
                exercise_type_proportions={
                    ExerciseType.STRENGTH: Decimal("0.5"),
                    ExerciseType.CARDIO: Decimal("0.25"),
                }
            )

    def test_request_rejects_out_of_range_proportions(self) -> None:
        for proportion in (Decimal("-0.1"), Decimal("1.1")):
            with self.subTest(proportion=proportion):
                with self.assertRaises(InvalidParameters):
                    build_request(
                        exercise_type_proportions={
                            ExerciseType.STRENGTH: proportion,
                            ExerciseType.CARDIO: Decimal("1") - proportion,
                        }
                    )

    def test_request_rejects_invalid_proportion_values(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_request(
                exercise_type_proportions={
                    ExerciseType.STRENGTH: "not-a-number",
                    ExerciseType.CARDIO: "0",
                }
            )

    def test_request_rejects_unknown_exercise_types(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_request(
                exercise_type_proportions={"unknown": Decimal("1")}
            )

    def test_request_rejects_duplicate_exercise_type_keys(self) -> None:
        with self.assertRaises(InvalidParameters):
            build_request(
                exercise_type_proportions={
                    "strength": Decimal("0.5"),
                    ExerciseType.STRENGTH: Decimal("0.5"),
                }
            )

    def test_request_rejects_empty_candidates(self) -> None:
        with self.assertRaises(InvalidParameters):
            build_request(candidate_exercises=())

    def test_request_rejects_non_exercise_candidates(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_request(candidate_exercises=(STRENGTH_CHEST, "not an exercise"))

    def test_request_rejects_non_muscle_group_coverage(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_request(covered_muscle_groups=(CHEST, 1))

    def test_request_rejects_non_positive_total_exercises(self) -> None:
        for total in (0, -1, True, 1.5):
            with self.subTest(total=total):
                with self.assertRaises(InvalidDomainValue):
                    build_request(total_exercises=total)


class StrategyRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.strength = StrengthFirstFakeStrategy()
        self.cardio = CardioFirstFakeStrategy()

    def test_registry_resolves_names_case_insensitively_and_trims_padding(self) -> None:
        registry = StrategyRegistry([self.strength, self.cardio])

        self.assertIs(registry.get("strength-first"), self.strength)
        self.assertIs(registry.get("  STRENGTH-FIRST  "), self.strength)
        self.assertIn("cardio-first", registry)
        self.assertEqual(len(registry), 2)

    def test_registry_lists_names_in_deterministic_order(self) -> None:
        registry = StrategyRegistry([self.strength, self.cardio])

        self.assertEqual(registry.names(), ("cardio-first", "strength-first"))

    def test_registry_rejects_unknown_names(self) -> None:
        registry = StrategyRegistry([self.strength])

        with self.assertRaises(UnknownGenerationStrategy) as context:
            registry.get("missing")

        self.assertIn("strength-first", str(context.exception))

    def test_registry_rejects_duplicate_names(self) -> None:
        registry = StrategyRegistry([self.strength])

        with self.assertRaises(InvalidDomainValue):
            registry.register(StrengthFirstFakeStrategy())

    def test_registry_rejects_invalid_strategy_objects(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            StrategyRegistry([object()])  # type: ignore[list-item]

    def test_registry_rejects_invalid_lookup_names(self) -> None:
        registry = StrategyRegistry([self.strength])

        for value in ("", "   ", None):
            with self.subTest(value=value):
                with self.assertRaises(InvalidDomainValue):
                    registry.get(value)  # type: ignore[arg-type]


class StrategyInterchangeabilityTests(unittest.TestCase):
    def test_same_request_can_be_processed_by_different_strategies(self) -> None:
        request = build_request(total_exercises=3)
        strength_result = StrengthFirstFakeStrategy().generate(request)
        cardio_result = CardioFirstFakeStrategy().generate(request)

        self.assertEqual(len(strength_result.exercises), 3)
        self.assertEqual(len(cardio_result.exercises), 3)
        self.assertEqual(
            [item.exercise.name for item in strength_result.exercises],
            ["Bench press", "Pull-up", "Jump rope"],
        )
        self.assertEqual(
            [item.exercise.name for item in cardio_result.exercises],
            ["Jump rope", "Bench press", "Pull-up"],
        )
        self.assertEqual(
            [item.order for item in strength_result.exercises],
            [1, 2, 3],
        )
        self.assertEqual(
            [item.order for item in cardio_result.exercises],
            [1, 2, 3],
        )

    def test_results_include_blocks_that_reference_selected_exercises(self) -> None:
        request = build_request(total_exercises=2)
        result = StrengthFirstFakeStrategy().generate(request)

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
            [1, 2],
        )

    def test_strategies_only_select_exercises_from_covered_muscle_groups(self) -> None:
        request = build_request(
            candidate_exercises=(
                STRENGTH_CHEST,
                CARDIO_CHEST,
                FLEXIBILITY_LEGS,
                STRENGTH_BACK,
            ),
            covered_muscle_groups=(LEGS,),
            total_exercises=4,
        )

        result = CardioFirstFakeStrategy().generate(request)

        self.assertEqual(
            [item.exercise.name for item in result.exercises],
            ["Hip opener"],
        )

    def test_generated_result_rejects_duplicate_order_values(self) -> None:
        with self.assertRaises(InvalidParameters):
            RoutineGenerationResult(
                exercises=(
                    GeneratedExercise(
                        exercise=STRENGTH_CHEST,
                        order=1,
                        sets=3,
                        repetitions=10,
                        rest_seconds=60,
                    ),
                    GeneratedExercise(
                        exercise=CARDIO_CHEST,
                        order=1,
                        sets=3,
                        repetitions=10,
                        rest_seconds=60,
                    ),
                ),
                block_structure=(),
            )

    def test_generated_exercise_validates_positive_values(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            GeneratedExercise(
                exercise=STRENGTH_CHEST,
                order=0,
                sets=3,
                repetitions=10,
                rest_seconds=60,
            )

    def test_generated_exercise_rejects_negative_rest(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            GeneratedExercise(
                exercise=STRENGTH_CHEST,
                order=1,
                sets=3,
                repetitions=10,
                rest_seconds=-1,
            )


if __name__ == "__main__":
    unittest.main()
