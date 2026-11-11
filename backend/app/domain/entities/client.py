from dataclasses import dataclass
from typing import Optional
from app.domain.entities.user import User


@dataclass
class Client:
    user: User
    age: int
    id_site: int
    id_client: Optional[int] = None

    def __post_init__(self):
        if self.id_client is None and self.user and self.user.id_user:
            self.id_client = self.user.id_user
        self.validate()

    def validate(self) -> None:
        if not self.user:
            raise ValueError("Client must be associated to a valid User.")
        if not self.user.is_client():
            raise ValueError(
                f"User with role '{self.user.role}' can not be set as Client."
            )
        if not (14 <= self.age <= 100):
            raise ValueError(
                f"Age ({self.age}) must be between 14 and 100."
            )
        if not self.id_site or self.id_site <= 0:
            raise ValueError("Client must be associated to a valid Site.")