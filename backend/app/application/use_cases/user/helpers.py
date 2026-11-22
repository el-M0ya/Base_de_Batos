"""Shared helpers for administrator-managed user accounts."""

from __future__ import annotations

from app.application.dto.actor import ActorDTO
from app.application.dto.user_dto import (
    ClientProfileInputDTO,
    CreateUserInputDTO,
    TrainerProfileInputDTO,
)
from app.application.exceptions import InvalidInput, PermissionDenied
from app.domain.entities.client import Client
from app.domain.entities.trainer import Trainer, TrainerSpecialty
from app.domain.entities.user import User
from app.domain.value_objects.user_role import UserRole


def require_admin(actor: ActorDTO) -> None:
    """Reject account-management operations performed by non-administrators."""
    if not actor.is_admin():
        raise PermissionDenied(
            "only administrators can manage user accounts; "
            f"the actor has the role {actor.role.value}."
        )


def build_user(input_dto: CreateUserInputDTO, *, user: User | None = None) -> User:
    """Build a validated user entity from account input data."""
    return build_account(
        name=input_dto.name,
        email=input_dto.email,
        password_hash=input_dto.password_hash,
        role=input_dto.role,
        user=user,
    )


def build_account(
    *,
    name: str,
    email: str,
    password_hash: str,
    role: UserRole | str,
    user: User | None = None,
) -> User:
    """Build a validated account without requiring profile input."""
    try:
        normalized_role = UserRole.from_value(role)
        return User(
            name=name,
            email=email,
            password_hash=password_hash,
            role=normalized_role,
            id_user=user.id_user if user is not None else None,
            created_at=user.created_at if user is not None else None,
            active=user.active if user is not None else True,
        )
    except ValueError as error:
        raise InvalidInput(str(error)) from error


def build_profile(
    user: User,
    trainer: TrainerProfileInputDTO | None,
    client: ClientProfileInputDTO | None,
) -> Trainer | Client | None:
    """Build the specialization entity selected for the user role."""
    try:
        if user.role is UserRole.TRAINER and trainer is not None:
            return Trainer(
                user=user,
                specialty=TrainerSpecialty(trainer.specialty),
            )
        if user.role is UserRole.CLIENT and client is not None:
            return Client(user=user, age=client.age, id_site=client.id_site)
    except ValueError as error:
        raise InvalidInput(str(error)) from error
    return None


def validate_update_profile(
    role: UserRole,
    trainer: TrainerProfileInputDTO | None,
    client: ClientProfileInputDTO | None,
) -> None:
    """Ensure an update does not create an inconsistent specialization."""
    if trainer is not None and client is not None:
        raise InvalidInput("a user can have only one specialization profile.")
    if role is UserRole.TRAINER and client is not None:
        raise InvalidInput("a trainer account cannot receive a client profile.")
    if role is UserRole.CLIENT and trainer is not None:
        raise InvalidInput("a client account cannot receive a trainer profile.")
    if role is UserRole.ADMIN and (trainer is not None or client is not None):
        raise InvalidInput(
            "an administrator account cannot receive a specialization profile."
        )


def attach_profile_id(
    profile: Trainer | Client | None,
    user: User,
) -> Trainer | Client | None:
    """Attach the persisted user identifier to its shared-key profile."""
    if profile is None or user.id_user is None:
        return profile
    if isinstance(profile, Trainer):
        profile.id_trainer = user.id_user
    else:
        profile.id_client = user.id_user
    return profile
