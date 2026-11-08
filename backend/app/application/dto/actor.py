"""Immutable DTO that represents the authenticated actor of a use case."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.value_objects.user_role import UserRole


@dataclass(frozen=True)
class ActorDTO:
    """User performing the operation and the role used to authorize it."""

    id_user: int
    role: UserRole

    def __post_init__(self) -> None:
        if (
            not isinstance(self.id_user, int)
            or isinstance(self.id_user, bool)
            or self.id_user <= 0
        ):
            raise InvalidDomainValue("id_user", self.id_user, "an integer greater than 0")
        object.__setattr__(self, "role", UserRole.from_value(self.role))

    def is_admin(self) -> bool:
        return self.role is UserRole.ADMIN

    def is_trainer(self) -> bool:
        return self.role is UserRole.TRAINER

    def is_client(self) -> bool:
        return self.role is UserRole.CLIENT
