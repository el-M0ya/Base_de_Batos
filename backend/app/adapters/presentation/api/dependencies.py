"""FastAPI dependencies for the exercise API."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from app.application.dto.actor import ActorDTO
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.dependencies import (
    ExerciseDependencies,
    build_exercise_dependencies,
)


async def get_exercise_dependencies() -> AsyncIterator[ExerciseDependencies]:
    """Build dependencies and keep one transaction open for the request."""
    dependencies = build_exercise_dependencies()
    async with dependencies.transaction.transaction():
        yield dependencies


def get_current_actor() -> ActorDTO:
    """Return the development actor until authentication is implemented."""
    environment = os.getenv("APP_ENV", "development").strip().lower()
    if environment not in {"development", "test"}:
        raise RuntimeError("Development actor injection is disabled outside development.")

    actor_id = int(os.getenv("DEV_ACTOR_ID", "1"))
    role = os.getenv("DEV_ACTOR_ROLE", UserRole.TRAINER.value)
    return ActorDTO(id_user=actor_id, role=role)
