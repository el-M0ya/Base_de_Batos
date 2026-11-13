"""Authorization helpers shared by catalog management use cases."""

from __future__ import annotations

from app.application.dto.actor import ActorDTO
from app.application.exceptions import PermissionDenied


def require_admin(actor: ActorDTO, operation: str) -> None:
    """Raise ``PermissionDenied`` unless the actor has the administrator role."""
    if not actor.is_admin():
        raise PermissionDenied(
            f"only administrators can {operation}; "
            f"the actor has the role {actor.role.value}."
        )
