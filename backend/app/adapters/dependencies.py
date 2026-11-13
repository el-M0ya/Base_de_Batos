"""FastAPI dependency providers.

Wires transaction boundaries, repositories, security adapters, catalog use cases
and site use cases together. Routers depend on these providers instead of
constructing infrastructure objects directly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.adapters.routers._errors import to_http_exception
from app.application.dto.actor import ActorDTO
from app.application.dto.auth_dto import UserSessionDTO
from app.application.exceptions import InvalidInput, InvalidToken
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.token_service import TokenService
from app.application.services.muscle_group_resolver import MuscleGroupResolver
from app.application.services.user_session_service import UserSessionService
from app.application.use_cases.authenticate_user import AuthenticateUserUseCase
from app.application.use_cases.create_muscle_group import CreateMuscleGroupUseCase
from app.application.use_cases.create_site import CreateSiteUseCase
from app.application.use_cases.create_training_program import (
    CreateTrainingProgramUseCase,
)
from app.application.use_cases.deactivate_site import DeactivateSiteUseCase
from app.application.use_cases.delete_muscle_group import DeleteMuscleGroupUseCase
from app.application.use_cases.delete_training_program import (
    DeleteTrainingProgramUseCase,
)
from app.application.use_cases.get_muscle_group import GetMuscleGroupUseCase
from app.application.use_cases.get_site import GetSiteUseCase
from app.application.use_cases.get_training_program import (
    GetTrainingProgramUseCase,
)
from app.application.use_cases.list_muscle_groups import ListMuscleGroupsUseCase
from app.application.use_cases.list_sites import ListSitesUseCase
from app.application.use_cases.list_training_programs import (
    ListTrainingProgramsUseCase,
)
from app.application.use_cases.resolve_session import ResolveSessionUseCase
from app.application.use_cases.reclassify_exercise import ReclassifyExerciseUseCase
from app.application.use_cases.set_training_program_muscle_groups import (
    SetTrainingProgramMuscleGroupsUseCase,
)
from app.application.use_cases.update_muscle_group import UpdateMuscleGroupUseCase
from app.application.use_cases.update_site import UpdateSiteUseCase
from app.application.use_cases.update_training_program import (
    UpdateTrainingProgramUseCase,
)
from app.core.config import get_settings
from app.domain.exceptions.domain_exceptions import DomainException
from app.domain.repositories.authorisation_repository import AuthorisationRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.user_role import UserRole
from app.infrastructure.persistence.repositories.authorisation_repository_sql import (
    AuthorisationRepositorySql,
)
from app.infrastructure.persistence.repositories.catalog_repository_sql import (
    CatalogRepositorySql,
)
from app.infrastructure.persistence.repositories.exercise_repository_sql import (
    ExerciseRepositorySql,
)
from app.infrastructure.persistence.repositories.muscle_group_repository_sql import (
    MuscleGroupRepositorySql,
)
from app.infrastructure.persistence.repositories.site_repository_sql import (
    SiteRepositorySql,
)
from app.infrastructure.persistence.repositories.user_repository_sql import (
    UserRepositorySql,
)
from app.infrastructure.persistence.repositories.workout_program_repository_sql import (
    WorkoutProgramRepositorySql,
)
from app.infrastructure.persistence.transaction import PsqlTransactionManager
from app.infrastructure.security.jwt_token_service import JwtTokenService
from app.infrastructure.security.password_hasher_bcrypt import BcryptPasswordHasher

_bearer_scheme = HTTPBearer(auto_error=False)

# Temporary administrator actor for catalog endpoints that predate the
# authentication layer. E4-01 replaces this for sites and authorisations, but
# the catalog routers still use it until they are migrated.
_DEFAULT_ACTOR = ActorDTO(id_user=1, role=UserRole.ADMIN)


async def get_transaction_manager() -> AsyncGenerator[PsqlTransactionManager, None]:
    """Yield a transaction manager bound to the current request."""
    tm = PsqlTransactionManager()
    async with tm:
        yield tm


# ---------------------------------------------------------------------------
# Persistence providers
# ---------------------------------------------------------------------------
def get_user_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> UserRepository:
    return UserRepositorySql(tm)


def get_authorisation_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> AuthorisationRepository:
    return AuthorisationRepositorySql(tm)


def get_site_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> SiteRepositorySql:
    return SiteRepositorySql(tm)


# ---------------------------------------------------------------------------
# Security providers
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


@lru_cache(maxsize=1)
def _token_service() -> TokenService:
    settings = get_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.jwt_access_token_expire_minutes,
    )


def get_password_hasher() -> PasswordHasher:
    return _password_hasher()


def get_token_service() -> TokenService:
    return _token_service()


def get_user_session_service(
    authorisations: AuthorisationRepository = Depends(get_authorisation_repository),
) -> UserSessionService:
    return UserSessionService(authorisations)


# ---------------------------------------------------------------------------
# Authentication use cases
# ---------------------------------------------------------------------------
def get_authenticate_user_use_case(
    users: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_password_hasher),
    tokens: TokenService = Depends(get_token_service),
    sessions: UserSessionService = Depends(get_user_session_service),
) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(users, hasher, tokens, sessions)


def get_resolve_session_use_case(
    users: UserRepository = Depends(get_user_repository),
    tokens: TokenService = Depends(get_token_service),
    sessions: UserSessionService = Depends(get_user_session_service),
) -> ResolveSessionUseCase:
    return ResolveSessionUseCase(users, tokens, sessions)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """Extract the bearer token or reject the request before opening a transaction."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Not authenticated.")
    if not credentials.credentials:
        raise _unauthorized("Not authenticated.")
    return credentials.credentials


async def get_current_session(
    token: str = Depends(get_bearer_token),
    use_case: ResolveSessionUseCase = Depends(get_resolve_session_use_case),
) -> UserSessionDTO:
    """Return the active session behind the request's bearer token."""
    try:
        return await use_case.execute(token)
    except InvalidToken as error:
        raise _unauthorized(error.detail) from error


def get_current_actor(
    session: UserSessionDTO = Depends(get_current_session),
) -> ActorDTO:
    """Return the actor used by application use cases."""
    return session.to_actor()


def require_admin(
    actor: ActorDTO = Depends(get_current_actor),
) -> ActorDTO:
    """Allow only administrators through the protected endpoint."""
    if not actor.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires the administrator role.",
        )
    return actor


# ---------------------------------------------------------------------------
# Site use cases
# ---------------------------------------------------------------------------
def get_create_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> CreateSiteUseCase:
    return CreateSiteUseCase(repo)


def get_get_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> GetSiteUseCase:
    return GetSiteUseCase(repo)


def get_update_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> UpdateSiteUseCase:
    return UpdateSiteUseCase(repo)


def get_deactivate_site_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> DeactivateSiteUseCase:
    return DeactivateSiteUseCase(repo)


def get_list_sites_use_case(
    repo: SiteRepositorySql = Depends(get_site_repository),
) -> ListSitesUseCase:
    return ListSitesUseCase(repo)


# ---------------------------------------------------------------------------
# Muscle-group catalog
# ---------------------------------------------------------------------------
async def get_muscle_group_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> AsyncGenerator[MuscleGroupRepositorySql, None]:
    """Yield a ``MuscleGroupRepositorySql`` using the given transaction manager."""
    yield MuscleGroupRepositorySql(tm)


async def get_create_muscle_group_use_case(
    repo: MuscleGroupRepositorySql = Depends(get_muscle_group_repository),
) -> AsyncGenerator[CreateMuscleGroupUseCase, None]:
    """Yield a ``CreateMuscleGroupUseCase``."""
    yield CreateMuscleGroupUseCase(repo)


async def get_update_muscle_group_use_case(
    repo: MuscleGroupRepositorySql = Depends(get_muscle_group_repository),
) -> AsyncGenerator[UpdateMuscleGroupUseCase, None]:
    """Yield an ``UpdateMuscleGroupUseCase``."""
    yield UpdateMuscleGroupUseCase(repo)


async def get_delete_muscle_group_use_case(
    repo: MuscleGroupRepositorySql = Depends(get_muscle_group_repository),
) -> AsyncGenerator[DeleteMuscleGroupUseCase, None]:
    """Yield a ``DeleteMuscleGroupUseCase``."""
    yield DeleteMuscleGroupUseCase(repo)


async def get_get_muscle_group_use_case(
    repo: MuscleGroupRepositorySql = Depends(get_muscle_group_repository),
) -> AsyncGenerator[GetMuscleGroupUseCase, None]:
    """Yield a ``GetMuscleGroupUseCase``."""
    yield GetMuscleGroupUseCase(repo)


async def get_list_muscle_groups_use_case(
    repo: MuscleGroupRepositorySql = Depends(get_muscle_group_repository),
) -> AsyncGenerator[ListMuscleGroupsUseCase, None]:
    """Yield a ``ListMuscleGroupsUseCase``."""
    yield ListMuscleGroupsUseCase(repo)


# ---------------------------------------------------------------------------
# Training programs and muscle-group coverage
# ---------------------------------------------------------------------------
async def get_workout_program_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> AsyncGenerator[WorkoutProgramRepositorySql, None]:
    """Yield a ``WorkoutProgramRepositorySql`` using the transaction manager."""
    yield WorkoutProgramRepositorySql(tm)


async def get_muscle_group_resolver(
    repo: MuscleGroupRepositorySql = Depends(get_muscle_group_repository),
) -> AsyncGenerator[MuscleGroupResolver, None]:
    """Yield a ``MuscleGroupResolver``."""
    yield MuscleGroupResolver(repo)


async def get_create_training_program_use_case(
    repo: WorkoutProgramRepositorySql = Depends(get_workout_program_repository),
    resolver: MuscleGroupResolver = Depends(get_muscle_group_resolver),
) -> AsyncGenerator[CreateTrainingProgramUseCase, None]:
    """Yield a ``CreateTrainingProgramUseCase``."""
    yield CreateTrainingProgramUseCase(repo, resolver)


async def get_update_training_program_use_case(
    repo: WorkoutProgramRepositorySql = Depends(get_workout_program_repository),
    resolver: MuscleGroupResolver = Depends(get_muscle_group_resolver),
) -> AsyncGenerator[UpdateTrainingProgramUseCase, None]:
    """Yield an ``UpdateTrainingProgramUseCase``."""
    yield UpdateTrainingProgramUseCase(repo, resolver)


async def get_delete_training_program_use_case(
    repo: WorkoutProgramRepositorySql = Depends(get_workout_program_repository),
) -> AsyncGenerator[DeleteTrainingProgramUseCase, None]:
    """Yield a ``DeleteTrainingProgramUseCase``."""
    yield DeleteTrainingProgramUseCase(repo)


async def get_get_training_program_use_case(
    repo: WorkoutProgramRepositorySql = Depends(get_workout_program_repository),
) -> AsyncGenerator[GetTrainingProgramUseCase, None]:
    """Yield a ``GetTrainingProgramUseCase``."""
    yield GetTrainingProgramUseCase(repo)


async def get_list_training_programs_use_case(
    repo: WorkoutProgramRepositorySql = Depends(get_workout_program_repository),
) -> AsyncGenerator[ListTrainingProgramsUseCase, None]:
    """Yield a ``ListTrainingProgramsUseCase``."""
    yield ListTrainingProgramsUseCase(repo)


async def get_set_training_program_muscle_groups_use_case(
    repo: WorkoutProgramRepositorySql = Depends(get_workout_program_repository),
    resolver: MuscleGroupResolver = Depends(get_muscle_group_resolver),
) -> AsyncGenerator[SetTrainingProgramMuscleGroupsUseCase, None]:
    """Yield a ``SetTrainingProgramMuscleGroupsUseCase``."""
    yield SetTrainingProgramMuscleGroupsUseCase(repo, resolver)


# ---------------------------------------------------------------------------
# Exercise bank and reclassification
# ---------------------------------------------------------------------------
async def get_exercise_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> AsyncGenerator[ExerciseRepositorySql, None]:
    """Yield an ``ExerciseRepositorySql`` using the given transaction manager."""
    yield ExerciseRepositorySql(tm)


async def get_catalog_repository(
    tm: PsqlTransactionManager = Depends(get_transaction_manager),
) -> AsyncGenerator[CatalogRepositorySql, None]:
    """Yield a ``CatalogRepositorySql`` using the given transaction manager."""
    yield CatalogRepositorySql(tm)


async def get_reclassify_exercise_use_case(
    exercises: ExerciseRepositorySql = Depends(get_exercise_repository),
    catalogs: CatalogRepositorySql = Depends(get_catalog_repository),
) -> AsyncGenerator[ReclassifyExerciseUseCase, None]:
    """Yield a ``ReclassifyExerciseUseCase`` with both repositories wired."""
    yield ReclassifyExerciseUseCase(exercises, catalogs)


async def get_actor(
    x_user_id: int = Header(default=1, alias="X-User-Id", ge=1),
    x_user_role: str = Header(default="TRAINER", alias="X-User-Role"),
) -> ActorDTO:
    """Return the provisional actor supplied by the request headers.

    Authentication is not yet wired into the exercise endpoints, so they read
    the actor from ``X-User-Id`` and ``X-User-Role``. The defaults keep local
    development usable.
    """
    try:
        return ActorDTO(
            id_user=x_user_id,
            role=UserRole.from_value(x_user_role),
        )
    except DomainException as error:
        raise to_http_exception(InvalidInput(str(error))) from error


def _admin_actor() -> ActorDTO:
    """Return the temporary administrator actor used by catalog routers."""
    return _DEFAULT_ACTOR
