"""Unit tests for the WorkoutProgram domain entity."""

import unittest

from app.domain.entities.workout_program import WorkoutProgram


class WorkoutProgramTests(unittest.TestCase):
    def test_initializes_without_target_muscle_groups(self) -> None:
        program = WorkoutProgram("Strength basics", "Build foundational strength")

        self.assertEqual(program.target_muscle_groups, [])

    def test_preserves_target_muscle_groups(self) -> None:
        groups = ["Chest", "Back"]

        program = WorkoutProgram("Upper body", "Improve upper-body strength", target_muscle_groups=groups)

        self.assertEqual(program.target_muscle_groups, groups)

    def test_rejects_empty_name(self) -> None:
        with self.assertRaises(ValueError):
            WorkoutProgram("", "Build strength")

    def test_rejects_empty_objective(self) -> None:
        with self.assertRaises(ValueError):
            WorkoutProgram("Strength basics", "   ")


if __name__ == "__main__":
    unittest.main()
