from dataclasses import dataclass
from enum import Enum
from typing import Optional
from app.domain.entities.user import User


class TrainerSpecialty(str, Enum):
    GENERAL = "GENERAL"
    HIPERTROFIA = "HIPERTROFIA"
    CARDIO = "CARDIO"
    REHABILITACION = "REHABILITACION"
    FUNCIONAL = "FUNCIONAL"
    ROUTINE_EDITOR = "ROUTINE_EDITOR"
    ROOM_CHIEF = "ROOM_CHIEF"


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

    def is_room_chief(self) -> bool:
        return self.specialty == TrainerSpecialty.ROOM_CHIEF