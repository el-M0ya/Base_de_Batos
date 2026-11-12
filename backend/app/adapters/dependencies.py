"""FastAPI dependency providers.

Wires transaction boundaries, repositories, security adapters and use cases
together. Routers depend on these providers instead of constructing
infrastructure objects directly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.dto.actor import ActorDTO
from app.application.dto.auth_dto import UserSessionDTO
from app.application.exceptions import InvalidToken
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.token_service import TokenService
from app.application.services.user_session_service import UserSessionService
from app.application.use_cases.authenticate_user import AuthenticateUserUseCase
from app.application.use_cases.create_site import CreateSiteUseCase
from app.application.use_cases.deactivate_site import DeactivateSiteUseCase
from app.application.use_cases.get_site import GetSiteUseCase
from app.application.use_cases.list_sites import ListSitesUseCase
from app.application.use_cases.resolve_session import ResolveSessionUseCase
from app.application.use_cases.update_site import UpdateSiteUseCase
from app.core.config import get_settings
from app.domain.repositories.authorisation_repository import AuthorisationRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.persistence.repositories.authorisation_repository_sql import (
    AuthorisationRepositorySql,
)
from app.infrastructure.persistence.repositories.site_repository_sql import (
    SiteRepositorySql,
)
from app.infrastructure.persistence.repositories.user_repository_sql import (
    UserRepositorySql,
)
from app.infrastructure.persistence.transaction import PsqlTransactionManager
from app.infrastructure.security.jwt_token_service import JwtTokenService
from app.infrastructure.security.password_hasher_bcrypt import BcryptPasswordHasher

_bearer_scheme = HTTPBearer(auto_error=False)


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
