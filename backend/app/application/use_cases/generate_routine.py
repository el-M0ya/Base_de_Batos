"""Use case that generates and persists a training routine (issue E6-02).

The use case coordinates four collaborators:

* the workout-program repository, which supplies the program, its covered
  muscle groups, and the trainer authorisation;
* the exercise repository, which supplies the candidate bank;
* the strategy registry, which resolves the requested generation algorithm;
* the routine repository, which persists the aggregate in one transaction.

The use case deliberately has no FastAPI or psycopg dependency. The caller must
run it inside the transaction manager that owns the repositories; the E2-07
routine repository writes the header, parameters, composition, and JSONB
structure in that single transaction.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_DOWN, Decimal, InvalidOperation

from app.application.dto.routine_generation_dto import (
    GenerateRoutineInputDTO,
    GeneratedRoutineOutputDTO,
)
from app.application.exceptions import (
    BusinessRuleViolation,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.routine import Routine
from app.domain.entities.routine_parameters import (
    IntensityLevel as RoutineIntensityLevel,
    RoutineParameters,
)
from app.domain.entities.routine_structure import RoutineStructure
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.exercise_repository import ExerciseRepository
from app.domain.repositories.routine_repository import RoutineRepository
from app.domain.repositories.workout_program_repository import (
    WorkoutProgramRepository,
)
from app.domain.strategies.routine_generation_strategy import (
    RoutineGenerationRequest,
    RoutineGenerationResult,
)
from app.domain.strategies.strategy_registry import StrategyRegistry
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel

# ``RoutineParameters`` and ``RoutineStructure`` require a positive identifier.
# The repository ignores this placeholder and assigns the identifier returned by
# the database; the use case updates both objects after the save.
_UNSAVED_ROUTINE_ID = 1

# Database ratios use two decimal places, so the output mirrors that precision.
_PERCENTAGE_QUANTUM = Decimal("0.01")


class GenerateRoutineUseCase:
    """Generate a routine through a strategy and persist it atomically."""

    def __init__(
        self,
        program_repository: WorkoutProgramRepository,
        exercise_repository: ExerciseRepository,
        routine_repository: RoutineRepository,
        strategy_registry: StrategyRegistry,
    ) -> None:
        self._programs = program_repository
        self._exercises = exercise_repository
        self._routines = routine_repository
        self._strategies = strategy_registry

    async def execute(
        self, request: GenerateRoutineInputDTO
    ) -> GeneratedRoutineOutputDTO:
        """Validate the request, run the strategy, and persist the result."""
        if not request.actor.is_trainer():
            raise PermissionDenied("only trainers can generate routines.")

        if request.total_exercises <= 0:
            raise InvalidInput("total_exercises must be greater than 0.")

        proportions = self._normalise_proportions(
            request.exercise_type_proportions
        )

        program = await self._programs.get_by_id(request.id_workout_program)
        if program is None:
            raise ResourceNotFound(
                "workout program", request.id_workout_program
            )

        program_id = program.id_workout_program
        if program_id is None:
            raise ResourceNotFound(
                "workout program", request.id_workout_program
            )

        authorisation = await self._programs.get_authorisation(
            request.actor.id_user, program_id
        )
        if authorisation is None or not authorisation.allows_generation_on(
            request.generation_date
        ):
            raise PermissionDenied(
                "the trainer does not have an active generation authorization "
                "for this program."
            )

        covered_groups = tuple(
            group
            for group in program.target_muscle_groups
            if group.id_muscle_group is not None
        )
        if not covered_groups:
            raise BusinessRuleViolation(
                "the workout program does not cover any muscle group."
            )

        candidates = await self._load_candidates(covered_groups)
        if not candidates:
            raise BusinessRuleViolation(
                "there are no exercises available for the program's covered "
                "muscle groups."
            )

        try:
            generation_request = RoutineGenerationRequest(
                candidate_exercises=candidates,
                target_intensity=request.target_intensity,
                exercise_type_proportions=proportions,
                total_exercises=request.total_exercises,
                covered_muscle_groups=covered_groups,
            )
            strategy = self._strategies.get(request.strategy_name)
            result = strategy.generate(generation_request)
        except DomainException as error:
            # Domain validation and strategy failures are input problems from
            # the caller's point of view.
            raise InvalidInput(str(error)) from error

        if not result.exercises:
            raise InvalidInput("the selected strategy returned no exercises.")
        if any(item.exercise.id_exercise is None for item in result.exercises):
            raise InvalidInput(
                "the selected strategy returned an exercise without an identifier."
            )

        try:
            parameters = self._build_parameters(
                total_exercises=request.total_exercises,
                proportions=proportions,
                covered_groups=covered_groups,
                target_intensity=request.target_intensity,
            )
            structure = RoutineStructure(
                id_routine=_UNSAVED_ROUTINE_ID,
                blocks=list(result.block_structure),
            )
            routine = Routine(
                id_workout_program=program_id,
                id_trainer_creator=request.actor.id_user,
                creation_date=request.generation_date,
            )
            # The E2-07 repository consumes these attributes as part of the
            # routine aggregate. They are attached immediately before the save.
            routine._parameters = parameters
            routine._contains = self._composition_entries(result)
        except DomainException as error:
            raise InvalidInput(str(error)) from error

        saved = await self._routines.save(routine, structure)
        if saved.id_routine is None:
            raise InvalidInput(
                "the routine repository did not return a persisted identifier."
            )

        # The output must expose the persisted identifiers, not the placeholders
        # required by the domain constructors.
        parameters.id_routine = saved.id_routine
        structure.id_routine = saved.id_routine

        return GeneratedRoutineOutputDTO(
            routine=saved,
            parameters=parameters,
            composition=tuple(result.exercises),
            structure=structure,
        )

    # ------------------------------------------------------------------
    # Validation and retrieval helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalise_proportions(
        raw_proportions: Mapping[object, object],
    ) -> dict[ExerciseType, Decimal]:
        """Validate fractions and return them keyed by the value object."""
        if not isinstance(raw_proportions, Mapping):
            raise InvalidInput(
                "exercise_type_proportions must be a mapping from exercise "
                "type to proportion."
            )

        normalised: dict[ExerciseType, Decimal] = {}
        for raw_type, raw_proportion in raw_proportions.items():
            try:
                exercise_type = ExerciseType.from_value(raw_type)
            except DomainException as error:
                raise InvalidInput(str(error)) from error

            if isinstance(raw_proportion, bool):
                raise InvalidInput(
                    f"the proportion for {exercise_type.value!r} must be a "
                    "number."
                )
            try:
                proportion = (
                    raw_proportion
                    if isinstance(raw_proportion, Decimal)
                    else Decimal(str(raw_proportion))
                )
            except (InvalidOperation, ValueError) as error:
                raise InvalidInput(
                    f"the proportion for {exercise_type.value!r} must be a "
                    "number."
                ) from error

            if not proportion.is_finite() or proportion < 0 or proportion > 1:
                raise InvalidInput(
                    f"the proportion for {exercise_type.value!r} must be "
                    "between 0 and 1."
                )
            if exercise_type in normalised:
                raise InvalidInput(
                    f"exercise type {exercise_type.value!r} appears more than "
                    "once."
                )
            normalised[exercise_type] = proportion

        if not normalised:
            raise InvalidInput(
                "at least one exercise type proportion is required."
            )

        total = sum(normalised.values(), Decimal("0"))
        if total != Decimal("1"):
            raise InvalidInput(
                f"exercise type proportions must sum to 1, got {total}."
            )
        return normalised

    async def _load_candidates(
        self, covered_groups: tuple[MuscleGroup, ...]
    ) -> tuple[Exercise, ...]:
        """Load and de-duplicate exercises from every covered muscle group."""
        by_identifier: dict[int, Exercise] = {}
        for group in covered_groups:
            if group.id_muscle_group is None:
                continue
            group_exercises = await self._exercises.list(
                muscle_group_id=group.id_muscle_group
            )
            for exercise in group_exercises:
                # Unpersisted exercises cannot be referenced by ``contains``.
                if exercise.id_exercise is not None:
                    by_identifier[exercise.id_exercise] = exercise

        return tuple(
            sorted(
                by_identifier.values(),
                key=lambda exercise: (
                    exercise.normalized_name,
                    exercise.id_exercise or 0,
                ),
            )
        )

    # ------------------------------------------------------------------
    # Aggregate construction helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _percentage(proportion: Decimal) -> Decimal:
        """Convert a [0, 1] fraction to the percentage stored in the routine.

        Rounding down keeps the sum of the three ratios at or below 100 even
        when the caller uses fractions with more than two decimal places.
        """
        return (proportion * Decimal("100")).quantize(
            _PERCENTAGE_QUANTUM, rounding=ROUND_DOWN
        )

    def _build_parameters(
        self,
        *,
        total_exercises: int,
        proportions: Mapping[ExerciseType, Decimal],
        covered_groups: tuple[MuscleGroup, ...],
        target_intensity: IntensityLevel,
    ) -> RoutineParameters:
        """Build the generation-parameter snapshot attached to the routine."""
        # The generation contract uses the Spanish/intensity value object while
        # the persisted routine parameters use the uppercase catalog names.
        routine_intensity = RoutineIntensityLevel[target_intensity.name]
        covered_ids = [
            group.id_muscle_group
            for group in covered_groups
            if group.id_muscle_group is not None
        ]
        return RoutineParameters(
            id_routine=_UNSAVED_ROUTINE_ID,
            total_exercises=total_exercises,
            intensity_level=routine_intensity,
            cardio_ratio=self._percentage(
                proportions.get(ExerciseType.CARDIO, Decimal("0"))
            ),
            strength_ratio=self._percentage(
                proportions.get(ExerciseType.STRENGTH, Decimal("0"))
            ),
            flexibility_ratio=self._percentage(
                proportions.get(ExerciseType.FLEXIBILITY, Decimal("0"))
            ),
            covered_muscle_group_ids=covered_ids,
        )

    @staticmethod
    def _composition_entries(
        result: RoutineGenerationResult,
    ) -> list[dict[str, int]]:
        """Map the strategy selection to the repository's composition shape."""
        return [
            {
                "id_exercise": item.exercise.id_exercise,
                "execution_order": item.order,
                "sets": item.sets,
                "repetitions": item.repetitions,
                "rest_time_seconds": item.rest_seconds,
            }
            for item in result.exercises
        ]
