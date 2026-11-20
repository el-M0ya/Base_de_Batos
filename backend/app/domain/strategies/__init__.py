"""Routine-generation strategies (Strategy pattern)."""

from app.domain.strategies.balanced_strategy import BalancedRoutineGenerationStrategy
from app.domain.strategies.routine_generation_strategy import (
    GeneratedExercise,
    RoutineGenerationRequest,
    RoutineGenerationResult,
    RoutineGenerationStrategy,
)
from app.domain.strategies.strategy_registry import StrategyRegistry

__all__ = [
    "BalancedRoutineGenerationStrategy",
    "GeneratedExercise",
    "RoutineGenerationRequest",
    "RoutineGenerationResult",
    "RoutineGenerationStrategy",
    "StrategyRegistry",
]
