"""Unit tests for the ``Exercise`` domain entity.

The suite covers creation, normalization, classification, authorship and the
basic invariants used for duplicate detection. It uses only the standard
library and the domain layer: no PostgreSQL, psycopg or FastAPI imports."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import date, datetime

from app.domain.entities.exercise import MAX_NAME_LENGTH, Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel


def build_exercise(**overrides: object) -> Exercise:
    """Create a valid exercise, overriding only the fields under test."""
    values: dict[str, object] = {
        "name": "Bench Press",
        "exercise_type": ExerciseType.STRENGTH,
        "intensity": IntensityLevel.MEDIUM,
        "muscle_group": MuscleGroup(1, "Chest"),
        "id_trainer_creator": 10,
    }
    values.update(overrides)
    return Exercise(**values)  # type: ignore[arg-type]


class ExerciseCreationTests(unittest.TestCase):
    def test_valid_exercise_uses_expected_defaults(self) -> None:
        exercise = build_exercise()

        self.assertIsNone(exercise.id_exercise)
        self.assertIsNone(exercise.description)
        self.assertIsInstance(exercise.registration_date, date)
        self.assertIs(exercise.exercise_type, ExerciseType.STRENGTH)
        self.assertIs(exercise.intensity, IntensityLevel.MEDIUM)
        self.assertEqual(exercise.muscle_group.id_muscle_group, 1)
        self.assertEqual(exercise.id_trainer_creator, 10)

    def test_exercise_type_and_intensity_accept_catalog_aliases(self) -> None:
        exercise = build_exercise(
            exercise_type="strength",
            intensity="high",
        )

        self.assertIs(exercise.exercise_type, ExerciseType.STRENGTH)
        self.assertIs(exercise.intensity, IntensityLevel.HIGH)

    def test_exercise_type_accepts_spanish_catalog_values(self) -> None:
        exercise = build_exercise(exercise_type="fuerza", intensity="alto")

        self.assertIs(exercise.exercise_type, ExerciseType.STRENGTH)
        self.assertIs(exercise.intensity, IntensityLevel.HIGH)

    def test_name_is_trimmed_and_internal_whitespace_is_collapsed(self) -> None:
        exercise = build_exercise(name="  Bench   Press  ")

        self.assertEqual(exercise.name, "Bench Press")

    def test_description_is_trimmed_and_blank_becomes_none(self) -> None:
        trimmed = build_exercise(description="  Barbell bench press  ")
        blank = build_exercise(description="   ")
        missing = build_exercise(description=None)

        self.assertEqual(trimmed.description, "Barbell bench press")
        self.assertIsNone(blank.description)
        self.assertIsNone(missing.description)

    def test_registration_date_can_be_provided(self) -> None:
        exercise = build_exercise(registration_date=date(2026, 1, 1))

        self.assertEqual(exercise.registration_date, date(2026, 1, 1))

    def test_optional_exercise_identifier_accepts_a_positive_value(self) -> None:
        exercise = build_exercise(id_exercise=7)

        self.assertEqual(exercise.id_exercise, 7)

    def test_exercise_is_immutable(self) -> None:
        exercise = build_exercise()

        with self.assertRaises(FrozenInstanceError):
            exercise.name = "Another name"  # type: ignore[misc]


class ExerciseValidationTests(unittest.TestCase):
    def test_name_must_be_a_non_empty_string(self) -> None:
        for value in (None, 123, "", "   "):
            with self.subTest(value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_exercise(name=value)

    def test_name_cannot_exceed_the_database_column_width(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_exercise(name="A" * (MAX_NAME_LENGTH + 1))

    def test_name_at_the_maximum_length_is_valid(self) -> None:
        exercise = build_exercise(name="A" * MAX_NAME_LENGTH)

        self.assertEqual(len(exercise.name), MAX_NAME_LENGTH)

    def test_description_must_be_text_or_none(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_exercise(description=123)

    def test_exercise_type_must_be_known(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_exercise(exercise_type="unknown")

    def test_intensity_must_be_known(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_exercise(intensity="extreme")

    def test_muscle_group_must_be_a_domain_value(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_exercise(muscle_group="Chest")

    def test_trainer_identifier_must_be_a_positive_integer(self) -> None:
        for value in (0, -1, True, "10"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_exercise(id_trainer_creator=value)

    def test_optional_exercise_identifier_must_be_positive(self) -> None:
        for value in (0, -1, True, "1"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidDomainValue):
                    build_exercise(id_exercise=value)

    def test_registration_date_must_be_a_date_not_a_datetime(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            build_exercise(registration_date=datetime(2026, 1, 1, 12, 0))


class ExerciseBehaviorTests(unittest.TestCase):
    def test_normalized_name_removes_case_accents_and_extra_whitespace(self) -> None:
        exercise = build_exercise(name="  Press   ÁÉ  ")

        self.assertEqual(exercise.normalized_name, "press ae")

    def test_normalized_name_is_stable_for_equivalent_names(self) -> None:
        first = build_exercise(name="Press ÁÉ")
        second = build_exercise(name="  press   ae ")

        self.assertEqual(first.normalized_name, second.normalized_name)

    def test_is_authored_by_compares_the_creator_identifier(self) -> None:
        exercise = build_exercise(id_trainer_creator=10)

        self.assertTrue(exercise.is_authored_by(10))
        self.assertFalse(exercise.is_authored_by(11))

    def test_belongs_to_muscle_group_compares_the_group_identifier(self) -> None:
        exercise = build_exercise(muscle_group=MuscleGroup(1, "Chest"))

        self.assertTrue(exercise.belongs_to_muscle_group(1))
        self.assertFalse(exercise.belongs_to_muscle_group(2))

    def test_same_normalized_name_in_another_group_is_a_different_classification(
        self,
    ) -> None:
        chest = build_exercise(
            name="Row",
            muscle_group=MuscleGroup(1, "Chest"),
        )
        back = build_exercise(
            name="Row",
            muscle_group=MuscleGroup(2, "Back"),
        )

        self.assertEqual(chest.normalized_name, back.normalized_name)
        self.assertNotEqual(
            chest.muscle_group.id_muscle_group,
            back.muscle_group.id_muscle_group,
        )


if __name__ == "__main__":
    unittest.main()