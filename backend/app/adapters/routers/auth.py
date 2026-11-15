"""Authentication endpoints (E4-01)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.dependencies import (
    get_authenticate_user_use_case,
    get_current_session,
)
from app.application.dto.auth_dto import LoginInputDTO, UserSessionDTO
from app.application.exceptions import AuthenticationFailed
from app.application.use_cases.authenticate_user import AuthenticateUserUseCase
from app.domain.value_objects.user_role import UserRole

router = APIRouter(prefix="/auth", tags=["auth"])

_ROLE_TO_API = {
    UserRole.ADMIN: "administrator",
    UserRole.TRAINER: "trainer",
    UserRole.CLIENT: "client",
}


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class CapabilitiesResponse(BaseModel):
    can_generate: bool
    can_validate: bool


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    capabilities: CapabilitiesResponse


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


def _user_response(session: UserSessionDTO) -> UserResponse:
    return UserResponse(
        id=session.id_user,
        email=session.email,
        role=_ROLE_TO_API[session.role],
        capabilities=CapabilitiesResponse(
            can_generate=session.capabilities.can_generate,
            can_validate=session.capabilities.can_validate,
        ),
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate with email and password",
)
async def login(
    request: LoginRequest,
    use_case: AuthenticateUserUseCase = Depends(get_authenticate_user_use_case),
) -> LoginResponse:
    """Validate credentials and return an expiring bearer token."""
    try:
        result = await use_case.execute(
            LoginInputDTO(email=request.email, password=request.password)
        )
    except AuthenticationFailed as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    return LoginResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
        user=_user_response(result.user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the authenticated user",
)
async def me(
    session: UserSessionDTO = Depends(get_current_session),
) -> UserResponse:
    """Return the identity, persisted role, and current capabilities."""
    return _user_response(session)
