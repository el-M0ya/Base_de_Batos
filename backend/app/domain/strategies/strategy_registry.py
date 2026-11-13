"""Registry of routine-generation strategies.

The registry is the only place that maps a stable strategy name to an
implementation. Callers depend on the ``RoutineGenerationStrategy`` contract,
never on a concrete algorithm."""

from __future__ import annotations

from collections.abc import Iterable

from app.domain.exceptions.domain_exceptions import (
    InvalidDomainValue,
    UnknownGenerationStrategy,
)
from app.domain.strategies.routine_generation_strategy import (
    RoutineGenerationStrategy,
)


class StrategyRegistry:
    """Small in-memory registry with case-insensitive lookup by name."""

    def __init__(
        self, strategies: Iterable[RoutineGenerationStrategy] = ()
    ) -> None:
        self._strategies: dict[str, RoutineGenerationStrategy] = {}
        for strategy in strategies:
            self.register(strategy)

    def register(self, strategy: RoutineGenerationStrategy) -> None:
        if not isinstance(strategy, RoutineGenerationStrategy):
            raise InvalidDomainValue(
                "strategy", strategy, "a RoutineGenerationStrategy instance"
            )

        name = strategy.name
        if not isinstance(name, str) or not name.strip():
            raise InvalidDomainValue(
                "strategy.name", name, "a non-empty string"
            )

        key = name.strip().lower()
        if key in self._strategies:
            raise InvalidDomainValue(
                "strategy.name", name, "a unique strategy name"
            )
        self._strategies[key] = strategy

    def get(self, name: str) -> RoutineGenerationStrategy:
        if not isinstance(name, str) or not name.strip():
            raise InvalidDomainValue("strategy.name", name, "a non-empty string")

        key = name.strip().lower()
        try:
            return self._strategies[key]
        except KeyError:
            raise UnknownGenerationStrategy(name, self.names()) from None

    def names(self) -> tuple[str, ...]:
        """Return the registered names in deterministic order."""
        return tuple(
            strategy.name for _, strategy in sorted(self._strategies.items())
        )

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False
        return name.strip().lower() in self._strategies

    def __len__(self) -> int:
        return len(self._strategies)
