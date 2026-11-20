"""Balanced routine-generation strategy (issue E6-01).

Selects exercises so that the number of exercises per type respects the
requested proportions (which sum to 1) and the total number of exercises, while
only using exercises whose muscle group is covered by the program (R9).
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.entities.routine_structure import BlockType, RoutineBlock
from app.domain.exceptions.domain_exceptions import InvalidParameters
from app.domain.strategies.routine_generation_strategy import (
    GeneratedExercise,
    RoutineGenerationRequest,
    RoutineGenerationResult,
    RoutineGenerationStrategy,
)
from app.domain.value_objects.exercise_type import ExerciseType

# Default prescription when the request does not specify per-exercise values.
DEFAULT_SETS = 3
DEFAULT_REPETITIONS = 10
DEFAULT_REST_SECONDS = 60


def _distribute_by_largest_remainder(
    total: int, proportions: dict[ExerciseType, Decimal]
) -> dict[ExerciseType, int]:
    """Distribute ``total`` items across exercise types (largest-remainder method).

    Guarantees the returned counts sum exactly to ``total`` and stay as close as
    possible to ``total * proportion`` for each type.
    """
    exact = {
        exercise_type: Decimal(total) * proportion
        for exercise_type, proportion in proportions.items()
    }
    counts = {exercise_type: int(value) for exercise_type, value in exact.items()}
    remaining = total - sum(counts.values())

    # Give the leftover slots to the types with the largest fractional remainders.
    ordered_types = sorted(
        exact.keys(),
        key=lambda exercise_type: (
            exact[exercise_type] - counts[exercise_type],
            str(exercise_type.value),
        ),
        reverse=True,
    )
    for exercise_type in ordered_types[:remaining]:
        counts[exercise_type] += 1

    return counts


class BalancedRoutineGenerationStrategy(RoutineGenerationStrategy):
    """Generates a routine whose type distribution matches the requested proportions.

    The strategy:

    1. Filters candidates to the muscle groups covered by the program (R9).
    2. Distributes ``total_exercises`` across exercise types according to
       ``exercise_type_proportions`` (which sum to 1).
    3. Prefers exercises matching ``target_intensity`` and falls back to other
       intensities of the same type only when needed.
    4. Raises :class:`InvalidParameters` naming the type that could not be filled
       when there are not enough candidates of a given type (CA-06).
    """

    _name = "balanced"

    @property
    def name(self) -> str:
        return self._name

    def generate(self, request: RoutineGenerationRequest) -> RoutineGenerationResult:
        covered_ids = {
            group.id_muscle_group for group in request.covered_muscle_groups
        }

        candidates = [
            exercise
            for exercise in request.candidate_exercises
            if not covered_ids
            or exercise.muscle_group.id_muscle_group in covered_ids
        ]

        target_count_by_type = _distribute_by_largest_remainder(
            request.total_exercises, request.exercise_type_proportions
        )

        selected: list[GeneratedExercise] = []
        order = 1

        for exercise_type, needed in target_count_by_type.items():
            if needed == 0:
                continue

            by_type = [
                exercise
                for exercise in candidates
                if exercise.exercise_type is exercise_type
            ]

            if len(by_type) < needed:
                raise InvalidParameters(
                    f"Not enough {exercise_type.value} exercises: "
                    f"{needed} required by the proportions, "
                    f"{len(by_type)} available in the covered muscle groups."
                )

            # Prefer the target intensity, keep a stable order within each group.
            preferred = [
                exercise
                for exercise in by_type
                if exercise.intensity is request.target_intensity
            ]
            fallback = [
                exercise
                for exercise in by_type
                if exercise.intensity is not request.target_intensity
            ]
            chosen = (preferred + fallback)[:needed]

            for exercise in chosen:
                selected.append(
                    GeneratedExercise(
                        exercise=exercise,
                        order=order,
                        sets=DEFAULT_SETS,
                        repetitions=DEFAULT_REPETITIONS,
                        rest_seconds=DEFAULT_REST_SECONDS,
                    )
                )
                order += 1

        blocks = [
            RoutineBlock(
                block_type=BlockType.SET,
                order=item.order,
                id_exercise=item.exercise.id_exercise,
                sets=item.sets,
                repetitions=item.repetitions,
                rest_seconds=item.rest_seconds,
            )
            for item in selected
        ]

        return RoutineGenerationResult(
            exercises=tuple(selected),
            block_structure=tuple(blocks),
        )
