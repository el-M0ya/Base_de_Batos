"""Composition helpers for the exercise API vertical slice.

This module is the infrastructure boundary where concrete PostgreSQL
repositories are assembled with application use cases. A request receives one
transaction manager, and every repository created for that request uses the
same connection.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.use_cases.create_exercise import CreateExerciseUseCase
from app.application.use_cases.list_exercise_catalogs import (
    ListExerciseCatalogsUseCase,
)
from app.application.use_cases.list_exercises import ListExercisesUseCase
from app.infrastructure.persistence.connection import get_db_pool
from app.infrastructure.persistence.repositories.catalog_repository_sql import (
    PostgresCatalogRepository,
)
from app.infrastructure.persistence.repositories.exercise_repository_sql import (
    PostgresExerciseRepository,
)
from app.infrastructure.persistence.transaction import PostgresTransactionManager


@dataclass(frozen=True)
class ExerciseDependencies:
    """Dependencies that participate in one request-scoped transaction."""

    transaction: PostgresTransactionManager
    create_exercise: CreateExerciseUseCase
    list_exercises: ListExercisesUseCase
    list_catalogs: ListExerciseCatalogsUseCase


def build_exercise_dependencies() -> ExerciseDependencies:
    """Construct the exercise use cases and their concrete repositories."""
    transaction = PostgresTransactionManager(get_db_pool())
    connection_provider = lambda: transaction.connection
    exercise_repository = PostgresExerciseRepository(connection_provider)
    catalog_repository = PostgresCatalogRepository(connection_provider)

    return ExerciseDependencies(
        transaction=transaction,
        create_exercise=CreateExerciseUseCase(
            exercise_repository,
            catalog_repository,
        ),
        list_exercises=ListExercisesUseCase(exercise_repository),
        list_catalogs=ListExerciseCatalogsUseCase(catalog_repository),
    )
