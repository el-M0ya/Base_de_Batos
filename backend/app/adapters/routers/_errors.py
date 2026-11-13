"""Map application and domain errors to FastAPI HTTP responses."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.domain.exceptions.domain_exceptions import DomainException


def to_http_exception(error: Exception) -> HTTPException:
    """Return the HTTP error that represents an application or domain error."""
    if isinstance(error, ResourceNotFound):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
    if isinstance(error, DuplicateResource):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error.detail,
        )
    if isinstance(error, BusinessRuleViolation):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error.detail,
        )
    if isinstance(error, PermissionDenied):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error.detail,
        )
    if isinstance(error, InvalidInput):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error.detail,
        )
    if isinstance(error, DomainException):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred.",
    )
