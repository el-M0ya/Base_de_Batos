"""FastAPI routes for administrator-managed users."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.adapters.schemas.user_schemas import (
    ClientProfileRequest,
    ClientProfileResponse,
    CreateUserRequest,
    TrainerProfileRequest,
    TrainerProfileResponse,
    UpdateUserRequest,
    UserResponse,
)
from app.application.dto.actor import ActorDTO
from app.application.dto.user_dto import (
    ClientProfileInputDTO,
    CreateUserInputDTO,
    TrainerProfileInputDTO,
    UpdateUserInputDTO,
    UserOutputDTO,
)
from app.application.exceptions import (
    ApplicationError,
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.application.use_cases.user.create_user import CreateUserUseCase
from app.application.use_cases.user.deactivate_user import DeactivateUserUseCase
from app.application.use_cases.user.list_users import ListUsersUseCase
from app.application.use_cases.user.update_user import UpdateUserUseCase
from app.domain.repositories.user_repository import UserRepository

ActorDependency = Callable[..., Awaitable[ActorDTO]]
RepositoryDependency = Callable[..., Awaitable[UserRepository]]
PasswordHasher = Callable[[str], str]


def build_user_router(
    get_actor: ActorDependency,
    get_repository: RepositoryDependency,
    hash_password: PasswordHasher,
) -> APIRouter:
    """Build the user router with authentication and persistence dependencies."""
    router = APIRouter(prefix="/users", tags=["Users"])
    actor_dependency = Depends(get_actor)
    repository_dependency = Depends(get_repository)

    @router.post(
        "",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_user(
        request: CreateUserRequest,
        actor: Annotated[ActorDTO, actor_dependency],
        repository: Annotated[UserRepository, repository_dependency],
    ) -> UserResponse:
        try:
            output = await CreateUserUseCase(repository).execute(
                CreateUserInputDTO(
                    actor=actor,
                    name=request.name,
                    email=request.email,
                    password_hash=hash_password(request.password),
                    role=request.role,
                    trainer=_trainer_input(request.trainer),
                    client=_client_input(request.client),
                )
            )
            return _response_from_output(output)
        except ApplicationError as error:
            raise _http_error(error) from error

    @router.get("", response_model=tuple[UserResponse, ...])
    async def list_users(
        actor: Annotated[ActorDTO, actor_dependency],
        repository: Annotated[UserRepository, repository_dependency],
    ) -> tuple[UserResponse, ...]:
        try:
            outputs = await ListUsersUseCase(repository).execute(actor)
            return tuple(_response_from_output(output) for output in outputs)
        except ApplicationError as error:
            raise _http_error(error) from error

    @router.get("/{id_user}", response_model=UserResponse)
    async def get_user(
        id_user: int,
        actor: Annotated[ActorDTO, actor_dependency],
        repository: Annotated[UserRepository, repository_dependency],
    ) -> UserResponse:
        try:
            if not actor.is_admin():
                raise PermissionDenied("only administrators can manage user accounts.")
            user = await repository.get_by_id(id_user)
            if user is None:
                raise ResourceNotFound("user", id_user)
            profile = await repository.get_profile(id_user)
            return _response_from_output(UserOutputDTO.from_entity(user, profile))
        except ApplicationError as error:
            raise _http_error(error) from error

    @router.patch("/{id_user}", response_model=UserResponse)
    async def update_user(
        id_user: int,
        request: UpdateUserRequest,
        actor: Annotated[ActorDTO, actor_dependency],
        repository: Annotated[UserRepository, repository_dependency],
    ) -> UserResponse:
        try:
            output = await UpdateUserUseCase(repository).execute(
                UpdateUserInputDTO(
                    actor=actor,
                    id_user=id_user,
                    name=request.name,
                    email=request.email,
                    password_hash=(
                        hash_password(request.password)
                        if request.password is not None
                        else None
                    ),
                    role=request.role,
                    active=request.active,
                    trainer=_trainer_input(request.trainer),
                    client=_client_input(request.client),
                )
            )
            return _response_from_output(output)
        except ApplicationError as error:
            raise _http_error(error) from error

    @router.delete("/{id_user}", response_model=UserResponse)
    async def deactivate_user(
        id_user: int,
        actor: Annotated[ActorDTO, actor_dependency],
        repository: Annotated[UserRepository, repository_dependency],
    ) -> UserResponse:
        try:
            output = await DeactivateUserUseCase(repository).execute(
                UpdateUserInputDTO(actor=actor, id_user=id_user)
            )
            return _response_from_output(output)
        except ApplicationError as error:
            raise _http_error(error) from error

    return router


def _trainer_input(
    request: TrainerProfileRequest | None,
) -> TrainerProfileInputDTO | None:
    return (
        TrainerProfileInputDTO(specialty=request.specialty)
        if request is not None
        else None
    )


def _client_input(
    request: ClientProfileRequest | None,
) -> ClientProfileInputDTO | None:
    return (
        ClientProfileInputDTO(age=request.age, id_site=request.id_site)
        if request is not None
        else None
    )


def _response_from_output(output: UserOutputDTO) -> UserResponse:
    return UserResponse(
        id_user=output.id_user,
        name=output.name,
        email=output.email,
        role=output.role,
        active=output.active,
        created_at=output.created_at,
        trainer=(
            TrainerProfileResponse.model_validate(output.trainer)
            if output.trainer is not None
            else None
        ),
        client=(
            ClientProfileResponse.model_validate(output.client)
            if output.client is not None
            else None
        ),
    )


def _http_error(error: ApplicationError) -> HTTPException:
    if isinstance(error, ResourceNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, DuplicateResource):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(error, PermissionDenied):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(error, InvalidInput):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(error, BusinessRuleViolation):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return HTTPException(status_code=status_code, detail=str(error))
