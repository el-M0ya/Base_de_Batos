"""Unit tests for the WorkoutProgram domain entity."""

import unittest

from app.domain.entities.muscle_group import MuscleGroup
from app.domain.entities.workout_program import WorkoutProgram
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


class WorkoutProgramTests(unittest.TestCase):
    def test_initializes_without_target_muscle_groups(self) -> None:
        program = WorkoutProgram("Strength basics", "Build foundational strength")

        self.assertEqual(program.target_muscle_groups, [])

    def test_preserves_target_muscle_groups(self) -> None:
        groups = [
            MuscleGroup(1, "Chest"),
            MuscleGroup(2, "Back"),
        ]

        program = WorkoutProgram(
            "Upper body",
            "Improve upper-body strength",
            target_muscle_groups=groups,
        )

        self.assertEqual(program.target_muscle_groups, groups)

    def test_normalizes_name_and_objective(self) -> None:
        program = WorkoutProgram("  Upper   body  ", "  Build   strength  ")

        self.assertEqual(program.name, "Upper body")
        self.assertEqual(program.objective, "Build strength")

    def test_rejects_empty_name(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            WorkoutProgram("", "Build strength")

    def test_rejects_empty_objective(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            WorkoutProgram("Strength basics", "   ")

    def test_rejects_non_positive_identifier(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            WorkoutProgram("Strength basics", "Build strength", id_workout_program=0)

    def test_rejects_non_muscle_group_coverage(self) -> None:
        with self.assertRaises(InvalidDomainValue):
            WorkoutProgram(
                "Strength basics",
                "Build strength",
                target_muscle_groups=["Chest"],  # type: ignore[list-item]
            )


if __name__ == "__main__":
    unittest.main()
