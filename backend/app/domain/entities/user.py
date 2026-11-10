from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.value_objects.user_role import UserRole


@dataclass
class User:
    name: str
    email: str
    password_hash: str
    role: UserRole
    id_user: Optional[int] = None
    created_at: Optional[datetime] = None
    active: bool = True

    def __post_init__(self):
        self.role = UserRole.from_value(self.role)
        self.validate()

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Username can not be empty.")
        if not self.email or "@" not in self.email:
            raise ValueError(f"Invalid email: '{self.email}'")
        if not self.password_hash:
            raise ValueError("No hashed password.")
        if not isinstance(self.active, bool):
            raise ValueError("User active status must be a boolean.")

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def is_trainer(self) -> bool:
        return self.role == UserRole.TRAINER

    def is_client(self) -> bool:
        return self.role == UserRole.CLIENT