"""Immutable DTOs that represent the authenticated actor of a use case."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.value_objects.user_role import UserRole


@dataclass(frozen=True)
class CapabilitiesDTO:
    """Capabilities derived from the actor's active trainer authorisations.

    Administrators and clients have no generation or validation capability.
    A trainer may have either or both, depending on the active rows in
    ``authorises``. Room chiefs are trainers whose ``can_validate`` is true.
    """

    can_generate: bool = False
    can_validate: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.can_generate, bool):
            raise InvalidDomainValue("can_generate", self.can_generate, "a boolean")
        if not isinstance(self.can_validate, bool):
            raise InvalidDomainValue("can_validate", self.can_validate, "a boolean")


@dataclass(frozen=True)
class ActorDTO:
    """User performing the operation, with role and optional capabilities.

    The first two fields intentionally remain the original contract so existing
    use cases can be migrated without changing their behaviour. Capabilities are
    optional and default to no permission; they do not replace the persisted
    role checks already performed by the use cases.
    """

    id_user: int
    role: UserRole
    capabilities: CapabilitiesDTO = field(default_factory=CapabilitiesDTO)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.id_user, int)
            or isinstance(self.id_user, bool)
            or self.id_user <= 0
        ):
            raise InvalidDomainValue("id_user", self.id_user, "an integer greater than 0")
        object.__setattr__(self, "role", UserRole.from_value(self.role))
        if not isinstance(self.capabilities, CapabilitiesDTO):
            raise InvalidDomainValue(
                "capabilities", self.capabilities, "a CapabilitiesDTO instance"
            )

    def is_admin(self) -> bool:
        return self.role is UserRole.ADMIN

    def is_trainer(self) -> bool:
        return self.role is UserRole.TRAINER

    def is_client(self) -> bool:
        return self.role is UserRole.CLIENT

    def can_generate(self) -> bool:
        return self.capabilities.can_generate

    def can_validate(self) -> bool:
        return self.capabilities.can_validate
