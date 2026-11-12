"""Administrative API for trainer-program authorizations."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.dependencies import _admin_actor, get_transaction_manager
from app.application.exceptions import DuplicateResource, InvalidInput
from app.domain.entities.authorisation import Authorisation
from app.domain.exceptions.domain_exceptions import DomainException
from app.infrastructure.persistence.repositories.authorisation_repository_sql import AuthorisationRepositorySql

router = APIRouter(prefix="/authorisations", tags=["authorisations"])


class AuthorisationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_trainer: int
    id_workout_program: int
    can_generate: bool = False
    can_validate: bool = False
    start_date: date = Field(default_factory=date.today)
    end_date: date | None = None


class AuthorisationOutput(AuthorisationInput):
    id_trainer: int
    id_workout_program: int


async def _repo(tm=Depends(get_transaction_manager)):
    return AuthorisationRepositorySql(tm)


def _entity(id_trainer: int, id_workout_program: int, data: AuthorisationInput) -> Authorisation:
    try:
        return Authorisation(id_trainer, id_workout_program, data.can_generate,
                             data.can_validate, data.start_date, data.end_date)
    except DomainException as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("", response_model=AuthorisationOutput, status_code=status.HTTP_201_CREATED)
async def create_authorisation(data: AuthorisationInput, repo=Depends(_repo)):
    _admin_actor()
    try:
        saved = await repo.create(_entity(data.id_trainer, data.id_workout_program, data))
    except (DuplicateResource, InvalidInput) as error:
        raise HTTPException(status_code=409 if isinstance(error, DuplicateResource) else 422, detail=str(error)) from error
    return AuthorisationOutput.model_validate(saved.__dict__)


@router.get("", response_model=list[AuthorisationOutput])
async def list_authorisations(id_trainer: int | None = Query(default=None, ge=1),
                              id_workout_program: int | None = Query(default=None, ge=1),
                              repo=Depends(_repo)):
    _admin_actor()
    return [AuthorisationOutput.model_validate(item.__dict__)
            for item in await repo.list(id_trainer, id_workout_program)]


@router.get("/{id_trainer}/{id_workout_program}", response_model=AuthorisationOutput)
async def get_authorisation(id_trainer: int = Path(ge=1), id_workout_program: int = Path(ge=1), repo=Depends(_repo)):
    _admin_actor()
    item = await repo.get(id_trainer, id_workout_program)
    if item is None:
        raise HTTPException(status_code=404, detail="Authorization not found")
    return AuthorisationOutput.model_validate(item.__dict__)


@router.get("/{id_trainer}/{id_workout_program}/allows/{operation}")
async def check_authorisation(id_trainer: int = Path(ge=1),
                              id_workout_program: int = Path(ge=1),
                              operation: str = Path(pattern="^(generate|validate)$"),
                              on_date: date | None = Query(default=None), repo=Depends(_repo)):
    """Check the requested capability for this program on a given date (today by default)."""
    _admin_actor()
    allowed = await repo.allows(id_trainer, id_workout_program, operation, on_date or date.today())
    return {"allowed": allowed}


@router.put("/{id_trainer}/{id_workout_program}", response_model=AuthorisationOutput)
async def update_authorisation(data: AuthorisationInput, id_trainer: int = Path(ge=1),
                               id_workout_program: int = Path(ge=1), repo=Depends(_repo)):
    _admin_actor()
    item = _entity(id_trainer, id_workout_program, data)
    try:
        saved = await repo.update(item)
    except InvalidInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if saved is None:
        raise HTTPException(status_code=404, detail="Authorization not found")
    return AuthorisationOutput.model_validate(saved.__dict__)


@router.delete("/{id_trainer}/{id_workout_program}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_authorisation(id_trainer: int = Path(ge=1), id_workout_program: int = Path(ge=1), repo=Depends(_repo)):
    _admin_actor()
    if not await repo.delete(id_trainer, id_workout_program):
        raise HTTPException(status_code=404, detail="Authorization not found")
