"""Pydantic schemas for exercise endpoints."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.application.dto.exercise_dto import (
    CatalogOutputDTO,
    ExerciseOutputDTO,
)


class CreateExerciseRequest(BaseModel):
    """Payload used to register an exercise."""

    name: str = Field(min_length=1, max_length=150)
    exercise_type: str
    intensity: str
    muscle_group_id: int = Field(gt=0)
    description: str | None = None
    registration_date: date | None = None


class ExerciseResponse(BaseModel):
    """Exercise representation exposed by the API."""

    model_config = ConfigDict(from_attributes=True)

    id_exercise: int
    name: str
    description: str | None
    registration_date: date
    exercise_type: str
    intensity: str
    muscle_group_id: int
    muscle_group_name: str
    trainer_id: int

    @classmethod
    def from_dto(cls, dto: ExerciseOutputDTO) -> "ExerciseResponse":
        return cls.model_validate(dto)


class CatalogResponse(BaseModel):
    """Catalog values used by the exercise form."""

    muscle_groups: list[dict[str, int | str]]
    exercise_types: list[str]
    intensity_levels: list[str]

    @classmethod
    def from_dto(cls, dto: CatalogOutputDTO) -> "CatalogResponse":
        return cls(
            muscle_groups=[
                {"id_muscle_group": item.id_muscle_group, "name": item.name}
                for item in dto.muscle_groups
            ],
            exercise_types=list(dto.exercise_types),
            intensity_levels=list(dto.intensity_levels),
        )
