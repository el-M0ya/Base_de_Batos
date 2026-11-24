"""Use case that retrieves a complete routine by identifier (issue E6-03).

Coordinates two collaborators:

* the routine repository, which loads the header, parameters, composition and
  nested JSONB structure atomically;
* the authorisation repository, which enforces program-level access.

The use case deliberately has no FastAPI or psycopg dependency. The caller runs
it inside the transaction manager that owns the repositories.
"""

from __future__ import annotations

from datetime import date

from app.application.dto.actor import ActorDTO
from app.application.dto.routine_generation_dto import GeneratedRoutineOutputDTO
from app.application.dto.routine_retrieval_dto import GetRoutineInputDTO
from app.application.exceptions import PermissionDenied, ResourceNotFound
from app.domain.repositories.authorisation_repository import AuthorisationRepository
from app.domain.repositories.routine_repository import RoutineRepository


class GetRoutineUseCase:
    """Retrieve a complete routine including its nested JSONB structure."""

    def __init__(
        self,
        routine_repository: RoutineRepository,
        authorisation_repository: AuthorisationRepository,
    ) -> None:
        self._routines = routine_repository
        self._authorisations = authorisation_repository

    async def execute(
        self, input_dto: GetRoutineInputDTO
    ) -> GeneratedRoutineOutputDTO:
        """Load the routine, authorize the actor, and return the aggregate.

        The composition is taken from the persisted ``contains`` rows attached
        to the routine entity by the repository. The structure is the
        deserialized JSONB document.
        """
        loaded = await self._routines.get_complete(input_dto.id_routine)
        if loaded is None:
            raise ResourceNotFound("routine", input_dto.id_routine)

        routine, structure = loaded

        await self._require_generation_authorisation(
            input_dto.actor, routine.id_workout_program
        )

        return GeneratedRoutineOutputDTO(
            routine=routine,
            parameters=routine._parameters,
            composition=self._composition_entries(routine),
            structure=structure,
        )

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    async def _require_generation_authorisation(
        self, actor: ActorDTO, id_workout_program: int
    ) -> None:
        """Require an effective ``can_generate`` grant for the routine's program.

        Only trainers can hold generation grants. The check reads the persisted
        ``authorises`` row instead of trusting a capability cached in the actor,
        so a grant created, revoked, or expired after login is honoured.
        """
        if not actor.is_trainer():
            raise PermissionDenied(
                "only trainers with an effective can_generate authorisation for the "
                "routine's program can perform this operation; "
                f"the actor has the role {actor.role.value}."
            )

        allowed = await self._authorisations.allows(
            actor.id_user, id_workout_program, "generate", date.today()
        )
        if not allowed:
            raise PermissionDenied(
                "the actor has no effective can_generate authorisation for the "
                f"workout program {id_workout_program} on {date.today().isoformat()}."
            )

    # ------------------------------------------------------------------
    # Composition mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _composition_entries(routine) -> tuple:
        """Map the persisted ``contains`` rows to a stable composition tuple.

        Each entry mirrors the shape produced by the generation strategy
        (``id_exercise``, ``execution_order``, ``sets``, ``repetitions``,
        ``rest_seconds``) so generation and retrieval share the same API
        representation.
        """
        contains = getattr(routine, "_contains", None) or []
        return tuple(
            {
                "id_exercise": entry["id_exercise"],
                "execution_order": entry["execution_order"],
                "sets": entry["sets"],
                "repetitions": entry["repetitions"],
                "rest_seconds": entry.get("rest_time_seconds", 60),
            }
            for entry in contains
        )
