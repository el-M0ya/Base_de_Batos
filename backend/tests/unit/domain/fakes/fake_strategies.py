"""Deterministic fake strategies used by the Strategy pattern tests."""

from __future__ import annotations

from typing import ClassVar

from app.domain.entities.routine_structure import BlockType, RoutineBlock
from app.domain.strategies.routine_generation_strategy import (
    GeneratedExercise,
    RoutineGenerationRequest,
    RoutineGenerationResult,
    RoutineGenerationStrategy,
)
from app.domain.value_objects.exercise_type import ExerciseType


class _PriorityFakeStrategy(RoutineGenerationStrategy):
    """Base fake that orders candidates by a fixed exercise-type priority."""

    _name: ClassVar[str]
    _priority: ClassVar[tuple[ExerciseType, ...]]
    _sets: ClassVar[int]
    _repetitions: ClassVar[int]
    _rest_seconds: ClassVar[int]

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

        priority = {
            exercise_type: position
            for position, exercise_type in enumerate(self._priority)
        }
        selected = sorted(
            candidates,
            key=lambda exercise: (
                priority.get(exercise.exercise_type, len(priority)),
                exercise.id_exercise or 0,
            ),
        )[: request.total_exercises]

        exercises: list[GeneratedExercise] = []
        blocks: list[RoutineBlock] = []
        for order, exercise in enumerate(selected, start=1):
            exercises.append(
                GeneratedExercise(
                    exercise=exercise,
                    order=order,
                    sets=self._sets,
                    repetitions=self._repetitions,
                    rest_seconds=self._rest_seconds,
                )
            )
            blocks.append(
                RoutineBlock(
                    block_type=BlockType.SET,
                    order=order,
                    id_exercise=exercise.id_exercise,
                    sets=self._sets,
                    repetitions=self._repetitions,
                    rest_seconds=self._rest_seconds,
                )
            )

        return RoutineGenerationResult(
            exercises=tuple(exercises),
            block_structure=tuple(blocks),
        )


class StrengthFirstFakeStrategy(_PriorityFakeStrategy):
    """Fake strategy that prioritises strength work."""

    _name = "strength-first"
    _priority = (
        ExerciseType.STRENGTH,
        ExerciseType.CARDIO,
        ExerciseType.FLEXIBILITY,
    )
    _sets = 4
    _repetitions = 8
    _rest_seconds = 120


class CardioFirstFakeStrategy(_PriorityFakeStrategy):
    """Fake strategy that prioritises cardiovascular work."""

    _name = "cardio-first"
    _priority = (
        ExerciseType.CARDIO,
        ExerciseType.STRENGTH,
        ExerciseType.FLEXIBILITY,
    )
    _sets = 3
    _repetitions = 15
    _rest_seconds = 60
