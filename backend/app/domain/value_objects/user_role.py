"""Persisted user roles (RF-03, R02).

The values are identical to the ones accepted by the ``app_user.role`` CHECK
constraint, so the domain can be mapped without translations.
"""

from __future__ import annotations

from enum import Enum

from app.domain.exceptions.domain_exceptions import InvalidDomainValue


class UserRole(str, Enum):
    """Roles that can be persisted for a user."""

    ADMIN = "ADMIN"
    TRAINER = "TRAINER"
    CLIENT = "CLIENT"

    @classmethod
    def from_value(cls, value: object) -> "UserRole":
        """Build the role from a stored value, ignoring case and padding."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            candidate = value.strip().upper()
            for role in cls:
                if role.value == candidate:
                    return role
        raise InvalidDomainValue(
            "role", value, f"one of {[role.value for role in cls]}"
        )
