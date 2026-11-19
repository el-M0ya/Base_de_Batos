"""API endpoints for client enrollments in workout programs."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, ConfigDict, Field

from app.application.dto.enrolment_dto import (
    CreateEnrolmentInputDTO,
    EnrolmentOutputDTO,
)
from app.application.exceptions import DuplicateResource, InvalidInput, ResourceNotFound
from app.application.use_cases.create_enrolment import CreateEnrolmentUseCase
from app.application.use_cases.list_client_enrolments import ListClientEnrolmentsUseCase
from app.infrastructure.persistence.connection import get_db_connection
from app.infrastructure.persistence.repositories.enrolment_repository_sql import (
    EnrolmentRepositorySql,
)

router = APIRouter(prefix="/enrolments", tags=["enrolments"])


class CreateEnrolmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_client: int = Field(ge=1)
    id_workout_program: int = Field(ge=1)
    enrollment_date: date = Field(default_factory=date.today)


async def _repository(connection=Depends(get_db_connection)) -> EnrolmentRepositorySql:
    return EnrolmentRepositorySql(connection)


@router.post("", response_model=EnrolmentOutputDTO, status_code=status.HTTP_201_CREATED)
async def create_enrolment(
    request: CreateEnrolmentRequest,
    repository: EnrolmentRepositorySql = Depends(_repository),
) -> EnrolmentOutputDTO:
    use_case = CreateEnrolmentUseCase(repository)
    try:
        return await use_case.execute(
            CreateEnrolmentInputDTO(
                id_client=request.id_client,
                id_workout_program=request.id_workout_program,
                enrollment_date=request.enrollment_date,
            )
        )
    except DuplicateResource as error:
        raise HTTPException(status_code=409, detail=error.detail) from error
    except ResourceNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/client/{id_client}", response_model=list[EnrolmentOutputDTO])
async def list_client_enrolments(
    id_client: int = Path(ge=1),
    repository: EnrolmentRepositorySql = Depends(_repository),
) -> list[EnrolmentOutputDTO]:
    use_case = ListClientEnrolmentsUseCase(repository)
    try:
        return list(await use_case.execute(id_client))
    except ResourceNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidInput as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
