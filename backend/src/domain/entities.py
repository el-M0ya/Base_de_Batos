from dataclasses import dataclass
from enum import Enum
from datetime import Optional
from src.domain.exceptions import InvalidEmailException, InvalidUserAge

# User Roles

class RoleEnum(str, Enum):
    ADMIN = "admin"
    TRAINER = "trainer"
    ROOM_CHIEF = "room_chief"
    CLIENT = "client"


# Site entity

@dataclass
class Site:
    id: Optional[int]
    name: str
    address: str

# User entity

@dataclass
class User:
    id: Optional[int]
    name: str
    age: int
    email: str
    password_hash: str
    role: RoleEnum
    site: Site

    def _is_valid_email(self, email: str) -> bool:
        return True

    def _is_valid_age(self, age: int) -> bool:
        return True

    def __post_init__(self):
        if not self._is_valid_email(self.email):
            raise InvalidEmailException(self.email)
        if not self._is_valid_age(self.age):
            raise InvalidUserAge(self.age)

@dataclass
class Trainer(User):
    specialty: str

@dataclass
class RoomChief(User):
    pass

@dataclass
class Client(User):
    # membership_id: int
    pass