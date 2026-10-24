from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional
from src.domain.exceptions import InvalidEmailException, InvalidUserAge

# User Roles

class RoleEnum(str, Enum):
    ADMIN = "admin"
    TRAINER = "trainer"
    CLIENT = "client"

class TrainerSpecialtyEnum(str, Enum):
    NORMAL = "normal" #normal trainer
    CREATOR = "creator" #creates and modifies routines
    ROOM_CHIEF = "room_chief" #validates routines

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
    email: str
    password_hash: str
    role: RoleEnum

    def _is_valid_email(self, email: str) -> bool:
        return True

    def _is_valid_age(self, age: int) -> bool:
        return True

    def __post_init__(self):
        if not self._is_valid_email(self.email):
            raise InvalidEmailException(self.email)

@dataclass
class Trainer(User):
    specialty: TrainerSpecialtyEnum

@dataclass
class Client(User):
    # membership_id: int
    age: int
    site_id: int

    def __post_init__(self):
        if not self._is_valid_email(self.email):
            raise InvalidEmailException(self.email)
        if not self._is_valid_age(self.age):
                raise InvalidUserAge(self.age)
    pass