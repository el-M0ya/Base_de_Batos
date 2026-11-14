"""Unit tests for exercise classification and duplicate-key behavior."""

import unittest
from datetime import date

from app.domain.entities.exercise import Exercise
from app.domain.entities.muscle_group import MuscleGroup
from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.value_objects.exercise_type import ExerciseType
from app.domain.value_objects.intensity_level import IntensityLevel


class ExerciseClassificationTests(unittest.TestCase):
    def test_converts_classification_aliases_to_domain_values(self) -> None:
        exercise = Exercise(
            name="  Bench   Press ",
            exercise_type="strength",
            intensity="high",
            muscle_group=MuscleGroup(1, "Chest"),
            id_trainer_creator=10,
            registration_date=date(2026, 1, 1),
        )

        self.assertIs(exercise.exercise_type, ExerciseType.STRENGTH)
        self.assertIs(exercise.intensity, IntensityLevel.HIGH)
        self.assertEqual(exercise.name, "Bench Press")

    def test_normalizes_name_for_duplicate_detection(self) -> None:
        exercise = Exercise(
            name=" Press   ÁÉ ",
            exercise_type=ExerciseType.CARDIO,
            intensity=IntensityLevel.MEDIUM,
            muscle_group=MuscleGroup(1, "Chest"),
            id_trainer_creator=10,
        )

        self.assertEqual(exercise.normalized_name, "press ae")

    def test_same_name_in_another_muscle_group_is_not_the_same_classification(self) -> None:
        chest_exercise = Exercise(
            "Row",
            ExerciseType.STRENGTH,
            IntensityLevel.MEDIUM,
            MuscleGroup(1, "Chest"),
            10,
        )
        back_exercise = Exercise(
            "Row",
            ExerciseType.STRENGTH,
            IntensityLevel.MEDIUM,
            MuscleGroup(2, "Back"),
            10,
        )

        self.assertEqual(chest_exercise.normalized_name, back_exercise.normalized_name)
        self.assertNotEqual(
            chest_exercise.muscle_group.id_muscle_group,
            back_exercise.muscle_group.id_muscle_group,
        )

    def test_rejects_an_unknown_exercise_type(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            Exercise(
                "Bench Press",
                "unknown",
                IntensityLevel.HIGH,
                MuscleGroup(1, "Chest"),
                10,
            )


class ExerciseReclassificationTests(unittest.TestCase):
    def test_reclassify_preserves_identity_and_updates_classification(self) -> None:
        original = Exercise(
            id_exercise=15,
            name="Remo con barra",
            exercise_type=ExerciseType.STRENGTH,
            intensity=IntensityLevel.HIGH,
            muscle_group=MuscleGroup(1, "Pectoral"),
            id_trainer_creator=10,
            description="Barra y banco",
            registration_date=date(2026, 1, 15),
        )
        back = MuscleGroup(2, "Espalda")

        reclassified = original.reclassify(
            exercise_type=ExerciseType.CARDIO,
            intensity=IntensityLevel.LOW,
            muscle_group=back,
        )

        self.assertIsNot(original, reclassified)
        self.assertEqual(reclassified.id_exercise, original.id_exercise)
        self.assertEqual(reclassified.name, original.name)
        self.assertEqual(reclassified.description, original.description)
        self.assertEqual(reclassified.registration_date, original.registration_date)
        self.assertEqual(reclassified.id_trainer_creator, original.id_trainer_creator)
        self.assertIs(reclassified.exercise_type, ExerciseType.CARDIO)
        self.assertIs(reclassified.intensity, IntensityLevel.LOW)
        self.assertEqual(reclassified.muscle_group, back)

        # The original entity is immutable and must keep its classification.
        self.assertIs(original.exercise_type, ExerciseType.STRENGTH)
        self.assertIs(original.intensity, IntensityLevel.HIGH)
        self.assertEqual(original.muscle_group.id_muscle_group, 1)

    def test_reclassify_validates_the_new_catalog_values(self) -> None:
        exercise = Exercise(
            "Press",
            ExerciseType.STRENGTH,
            IntensityLevel.MEDIUM,
            MuscleGroup(1, "Pectoral"),
            10,
        )

        with self.assertRaises(InvalidDomainValue):
            exercise.reclassify(
                exercise_type=ExerciseType.STRENGTH,
                intensity="extremo",
                muscle_group=MuscleGroup(2, "Espalda"),
            )


if __name__ == "__main__":
    unittest.main()
