"""Authorization helpers shared by application use cases."""

from __future__ import annotations

from datetime import date

from app.application.dto.actor import ActorDTO
from app.application.exceptions import PermissionDenied
from app.domain.repositories.authorisation_repository import AuthorisationRepository


def require_admin(actor: ActorDTO, operation: str) -> None:
    """Raise ``PermissionDenied`` unless the actor has the administrator role."""
    if not actor.is_admin():
        raise PermissionDenied(
            f"only administrators can {operation}; "
            f"the actor has the role {actor.role.value}."
        )


async def require_validation_authorisation(
    actor: ActorDTO,
    id_workout_program: int,
    on_date: date,
    authorisations: AuthorisationRepository,
) -> None:
    """Require an effective ``can_validate`` grant for a workout program.

    Only trainers can hold validation grants. The check reads the persisted
    ``authorises`` row instead of trusting a capability cached in the actor, so
    a grant created, revoked, or expired after login is honoured.
    """
    if not actor.is_trainer():
        raise PermissionDenied(
            "only trainers with an effective can_validate authorisation for the "
            "routine's program can perform this operation; "
            f"the actor has the role {actor.role.value}."
        )

    allowed = await authorisations.allows(
        actor.id_user,
        id_workout_program,
        "validate",
        on_date,
    )
    if not allowed:
        raise PermissionDenied(
            "the actor has no effective can_validate authorisation for the "
            f"workout program {id_workout_program} on {on_date.isoformat()}."
        )
