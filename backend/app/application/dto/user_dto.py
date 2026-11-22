"""DTOs for administrator-managed user accounts and profiles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.application.dto.actor import ActorDTO
from app.domain.entities.client import Client
from app.domain.entities.trainer import Trainer, TrainerSpecialty
from app.domain.entities.user import User
from app.domain.exceptions.domain_exceptions import InvalidDomainValue
from app.domain.value_objects.user_role import UserRole


@dataclass(frozen=True)
class TrainerProfileInputDTO:
    """Trainer specialization data supplied by an account administrator."""

    specialty: str = TrainerSpecialty.GENERAL.value

    def __post_init__(self) -> None:
        if not isinstance(self.specialty, str):
            raise InvalidDomainValue(
                "specialty", self.specialty, "a valid trainer specialty"
            )
        try:
            specialty = TrainerSpecialty(self.specialty.strip().upper())
        except ValueError as error:
            raise InvalidDomainValue(
                "specialty",
                self.specialty,
                f"one of {[value.value for value in TrainerSpecialty]}",
            ) from error
        object.__setattr__(self, "specialty", specialty.value)


@dataclass(frozen=True)
class ClientProfileInputDTO:
    """Client specialization data supplied by an account administrator."""

    age: int
    id_site: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.age, int)
            or isinstance(self.age, bool)
            or not 14 <= self.age <= 100
        ):
            raise InvalidDomainValue("age", self.age, "an integer between 14 and 100")
        if (
            not isinstance(self.id_site, int)
            or isinstance(self.id_site, bool)
            or self.id_site <= 0
        ):
            raise InvalidDomainValue("id_site", self.id_site, "an integer greater than 0")


@dataclass(frozen=True)
class CreateUserInputDTO:
    """Data required to create a user and its optional specialization profile."""

    actor: ActorDTO
    name: str
    email: str
    password_hash: str
    role: UserRole | str
    trainer: Optional[TrainerProfileInputDTO] = None
    client: Optional[ClientProfileInputDTO] = None

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        role = UserRole.from_value(self.role)
        object.__setattr__(self, "role", role)
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidDomainValue("name", self.name, "a non-empty string")
        if not isinstance(self.email, str) or not self.email.strip():
            raise InvalidDomainValue("email", self.email, "a non-empty string")
        if not isinstance(self.password_hash, str) or not self.password_hash:
            raise InvalidDomainValue("password_hash", self.password_hash, "a non-empty string")
        _validate_profile_for_role(role, self.trainer, self.client)


@dataclass(frozen=True)
class UpdateUserInputDTO:
    """Partial account and profile changes requested by an administrator."""

    actor: ActorDTO
    id_user: int
    name: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    role: Optional[UserRole | str] = None
    active: Optional[bool] = None
    trainer: Optional[TrainerProfileInputDTO] = None
    client: Optional[ClientProfileInputDTO] = None

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        if (
            not isinstance(self.id_user, int)
            or isinstance(self.id_user, bool)
            or self.id_user <= 0
        ):
            raise InvalidDomainValue("id_user", self.id_user, "an integer greater than 0")
        if self.role is not None:
            object.__setattr__(self, "role", UserRole.from_value(self.role))
        if self.name is not None and (
            not isinstance(self.name, str) or not self.name.strip()
        ):
            raise InvalidDomainValue("name", self.name, "a non-empty string")
        if self.email is not None and (
            not isinstance(self.email, str) or not self.email.strip()
        ):
            raise InvalidDomainValue("email", self.email, "a non-empty string")
        if self.password_hash is not None and (
            not isinstance(self.password_hash, str) or not self.password_hash
        ):
            raise InvalidDomainValue(
                "password_hash", self.password_hash, "a non-empty string"
            )
        if self.active is not None and not isinstance(self.active, bool):
            raise InvalidDomainValue("active", self.active, "a boolean")
        if self.trainer is not None and self.client is not None:
            raise InvalidDomainValue(
                "profile", "trainer and client", "only one specialization profile"
            )


@dataclass(frozen=True)
class TrainerProfileOutputDTO:
    """Trainer specialization data returned to an administrator."""

    id_trainer: int
    specialty: str

    @classmethod
    def from_entity(cls, trainer: Trainer) -> "TrainerProfileOutputDTO":
        if trainer.id_trainer is None:
            raise InvalidDomainValue(
                "id_trainer", trainer.id_trainer, "a persisted trainer"
            )
        return cls(id_trainer=trainer.id_trainer, specialty=trainer.specialty.value)


@dataclass(frozen=True)
class ClientProfileOutputDTO:
    """Client specialization data returned to an administrator."""

    id_client: int
    age: int
    id_site: int

    @classmethod
    def from_entity(cls, client: Client) -> "ClientProfileOutputDTO":
        if client.id_client is None:
            raise InvalidDomainValue(
                "id_client", client.id_client, "a persisted client"
            )
        return cls(
            id_client=client.id_client,
            age=client.age,
            id_site=client.id_site,
        )


@dataclass(frozen=True)
class UserOutputDTO:
    """Account and specialization data returned to an administrator."""

    id_user: int
    name: str
    email: str
    role: str
    active: bool
    created_at: Optional[datetime]
    trainer: Optional[TrainerProfileOutputDTO] = None
    client: Optional[ClientProfileOutputDTO] = None

    @classmethod
    def from_entity(
        cls,
        user: User,
        profile: Optional[Trainer | Client] = None,
    ) -> "UserOutputDTO":
        if user.id_user is None:
            raise InvalidDomainValue("id_user", user.id_user, "a persisted user")
        trainer = (
            TrainerProfileOutputDTO.from_entity(profile)
            if isinstance(profile, Trainer)
            else None
        )
        client = (
            ClientProfileOutputDTO.from_entity(profile)
            if isinstance(profile, Client)
            else None
        )
        return cls(
            id_user=user.id_user,
            name=user.name,
            email=user.email,
            role=user.role.value,
            active=user.active,
            created_at=user.created_at,
            trainer=trainer,
            client=client,
        )


def _validate_profile_for_role(
    role: UserRole,
    trainer: Optional[TrainerProfileInputDTO],
    client: Optional[ClientProfileInputDTO],
) -> None:
    if trainer is not None and client is not None:
        raise InvalidDomainValue(
            "profile", "trainer and client", "only one specialization profile"
        )
    if role is UserRole.TRAINER and trainer is None:
        raise InvalidDomainValue("trainer", trainer, "a trainer profile")
    if role is UserRole.CLIENT and client is None:
        raise InvalidDomainValue("client", client, "a client profile")
    if role is not UserRole.TRAINER and trainer is not None:
        raise InvalidDomainValue("trainer", trainer, "only a trainer account")
    if role is not UserRole.CLIENT and client is not None:
        raise InvalidDomainValue("client", client, "only a client account")
