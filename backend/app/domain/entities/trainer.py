from dataclasses import dataclass
from enum import Enum
from typing import Optional
from app.domain.entities.user import User
from app.domain.entities.authorisation import Authorisation
from datetime import date


class TrainerSpecialty(str, Enum):
    GENERAL = "GENERAL"
    HIPERTROFIA = "HIPERTROFIA"
    CARDIO = "CARDIO"
    REHABILITACION = "REHABILITACION"
    FUNCIONAL = "FUNCIONAL"
    ROUTINE_EDITOR = "ROUTINE_EDITOR"


@dataclass
class Trainer:
    user: User
    specialty: TrainerSpecialty = TrainerSpecialty.GENERAL
    id_trainer: Optional[int] = None

    def __post_init__(self):
        if isinstance(self.specialty, str):
            self.specialty = TrainerSpecialty(self.specialty)
        if self.id_trainer is None and self.user and self.user.id_user:
            self.id_trainer = self.user.id_user
        self.validate()

    def validate(self) -> None:
        if not self.user:
            raise ValueError("The trainer must be associated with a valid user.")
        if not self.user.is_trainer():
            raise ValueError(
                f"The user with role '{self.user.role}' cannot be registered as a Trainer."
            )

    def is_room_chief(self, authorisation: Authorisation, on_date: date) -> bool:
        """Room-chief capability is a current validation permission per program."""
        return (
            authorisation.id_trainer == self.id_trainer
            and authorisation.allows_validation_on(on_date)
        )
