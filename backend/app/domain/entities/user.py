from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    TRAINER = "TRAINER"
    CLIENT = "CLIENT"


@dataclass
class User:
    name: str
    email: str
    password_hash: str
    role: UserRole
    id_user: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if isinstance(self.role, str):
            self.role = UserRole(self.role)
        self.validate()

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Username can not be empty.")
        if not self.email or "@" not in self.email:
            raise ValueError(f"Invalid email: '{self.email}'")
        if not self.password_hash:
            raise ValueError("No hashed password.")

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def is_trainer(self) -> bool:
        return self.role == UserRole.TRAINER

    def is_client(self) -> bool:
        return self.role == UserRole.CLIENT