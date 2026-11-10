from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WorkoutProgram:
    name: str
    objective: str
    id_workout_program: Optional[int] = None
    target_muscle_groups: Optional[List[str]] = None

    def __post_init__(self):
        """Initialize covered muscle groups and enforce program invariants."""
        if self.target_muscle_groups is None:
            self.target_muscle_groups = []
        self.validate()

    def validate(self) -> None:
        """Ensure the program has a name and an objective."""
        if not self.name or not self.name.strip():
            raise ValueError("The workout program name cannot be empty.")
        if not self.objective or not self.objective.strip():
            raise ValueError("The workout program objective cannot be empty.")