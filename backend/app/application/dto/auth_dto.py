"""DTOs for authentication and session resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.application.dto.actor import ActorDTO, CapabilitiesDTO
from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.value_objects.user_role import UserRole


@dataclass(frozen=True)
class LoginInputDTO:
    """Credentials supplied by a user who wants to start a session."""

    email: str
    password: str

    def __post_init__(self) -> None:
        if not isinstance(self.email, str) or not self.email.strip():
            raise InvalidDomainValue("email", self.email, "a non-empty email")
        if not isinstance(self.password, str) or not self.password:
            raise InvalidDomainValue("password", self.password, "a non-empty password")


@dataclass(frozen=True)
class UserSessionDTO:
    """Authenticated identity, persisted role, and derived capabilities."""

    id_user: int
    email: str
    role: UserRole
    capabilities: CapabilitiesDTO = field(default_factory=CapabilitiesDTO)
    active: bool = True

    def __post_init__(self) -> None:
        if (
            not isinstance(self.id_user, int)
            or isinstance(self.id_user, bool)
            or self.id_user <= 0
        ):
            raise InvalidDomainValue("id_user", self.id_user, "an integer greater than 0")
        if not isinstance(self.email, str) or not self.email.strip():
            raise InvalidDomainValue("email", self.email, "a non-empty email")
        object.__setattr__(self, "role", UserRole.from_value(self.role))
        if not isinstance(self.capabilities, CapabilitiesDTO):
            raise InvalidDomainValue(
                "capabilities", self.capabilities, "a CapabilitiesDTO instance"
            )
        if not isinstance(self.active, bool):
            raise InvalidDomainValue("active", self.active, "a boolean")

    def to_actor(self) -> ActorDTO:
        """Return the actor representation consumed by existing use cases."""
        return ActorDTO(
            id_user=self.id_user,
            role=self.role,
            capabilities=self.capabilities,
        )


@dataclass(frozen=True)
class IssuedSessionDTO:
    """Result of a successful login, including the expiring access token."""

    access_token: str
    token_type: str
    expires_at: datetime
    user: UserSessionDTO

    @property
    def expires_in(self) -> int:
        """Return remaining lifetime in whole seconds, never negative."""
        from datetime import timezone

        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return max(0, int((expires_at - now).total_seconds()))
