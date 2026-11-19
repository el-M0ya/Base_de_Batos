"""Map application and domain errors to the public API error contract.

Every error response has the same top-level shape::

    {"message": "...", "code": "STABLE_CODE", "details": {...} | null}

The ``code`` is the stable part clients can branch on. ``message`` is
human-readable and may change without notice, while ``details`` contains
structured context such as the missing resource or the conflicting exercise.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)
from app.domain.exceptions.domain_exceptions import DomainException

logger = logging.getLogger(__name__)

# Stable error codes exposed to API clients.
EXERCISE_NOT_FOUND = "EXERCISE_NOT_FOUND"
MUSCLE_GROUP_NOT_FOUND = "MUSCLE_GROUP_NOT_FOUND"
RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
EXERCISE_DUPLICATE = "EXERCISE_DUPLICATE"
DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
PERMISSION_DENIED = "PERMISSION_DENIED"
INVALID_INPUT = "INVALID_INPUT"
VALIDATION_ERROR = "VALIDATION_ERROR"
HTTP_ERROR = "HTTP_ERROR"
INTERNAL_ERROR = "INTERNAL_ERROR"

# Starlette renamed the 422 constant; use the numeric value so the adapter
# stays compatible with the minimum FastAPI version supported by the project.
UNPROCESSABLE_CONTENT = 422


def _payload(
    message: str,
    code: str,
    details: Optional[object] = None,
) -> dict:
    """Build the uniform error body."""
    return {"message": message, "code": code, "details": details}


def _not_found_code(resource: str) -> str:
    """Return the most specific stable code for a missing resource."""
    normalized = resource.strip().lower().replace("_", " ")
    if normalized == "exercise":
        return EXERCISE_NOT_FOUND
    if normalized in {"muscle group", "muscle groups"}:
        return MUSCLE_GROUP_NOT_FOUND
    return RESOURCE_NOT_FOUND


def _duplicate_code(resource: str) -> str:
    """Return the most specific stable code for a duplicate resource."""
    normalized = resource.strip().lower()
    if normalized == "exercise":
        return EXERCISE_DUPLICATE
    return DUPLICATE_RESOURCE


def _existing_summary(existing: Optional[object]) -> Optional[dict]:
    """Extract a JSON-safe summary of the resource that caused a conflict."""
    if existing is None:
        return None

    summary: dict = {}
    for attribute in (
        "id_exercise",
        "id_muscle_group",
        "id_site",
        "id_workout_program",
        "id_trainer",
    ):
        value = getattr(existing, attribute, None)
        if value is not None:
            summary[attribute] = value

    name = getattr(existing, "name", None)
    if name is not None:
        summary["name"] = name

    muscle_group = getattr(existing, "muscle_group", None)
    if muscle_group is not None:
        summary["muscle_group_id"] = getattr(
            muscle_group, "id_muscle_group", None
        )

    return summary or None


def to_http_exception(error: Exception) -> HTTPException:
    """Return the HTTP error that represents an application or domain error."""
    if isinstance(error, ResourceNotFound):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_payload(
                str(error),
                _not_found_code(error.resource),
                {"resource": error.resource, "identifier": error.identifier},
            ),
        )
    if isinstance(error, DuplicateResource):
        details = {
            "resource": error.resource,
            "existing": _existing_summary(error.existing),
        }
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_payload(
                error.detail,
                _duplicate_code(error.resource),
                details,
            ),
        )
    if isinstance(error, BusinessRuleViolation):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_payload(error.detail, BUSINESS_RULE_VIOLATION),
        )
    if isinstance(error, PermissionDenied):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_payload(error.detail, PERMISSION_DENIED),
        )
    if isinstance(error, InvalidInput):
        return HTTPException(
            status_code=UNPROCESSABLE_CONTENT,
            detail=_payload(error.detail, INVALID_INPUT),
        )
    if isinstance(error, DomainException):
        return HTTPException(
            status_code=UNPROCESSABLE_CONTENT,
            detail=_payload(str(error), INVALID_INPUT),
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=_payload("An unexpected error occurred.", INTERNAL_ERROR),
    )


async def http_exception_handler(
    request: Request,
    error: HTTPException,
) -> JSONResponse:
    """Render our payloads directly and wrap framework HTTP errors uniformly."""
    detail = error.detail
    if isinstance(detail, dict) and "message" in detail and "code" in detail:
        return JSONResponse(
            status_code=error.status_code,
            content={
                "message": detail["message"],
                "code": detail["code"],
                "details": detail.get("details"),
            },
            headers=error.headers,
        )

    if isinstance(detail, str):
        message = detail
        details = None
    else:
        message = "The request could not be processed."
        details = detail

    return JSONResponse(
        status_code=error.status_code,
        content=_payload(message, HTTP_ERROR, details),
        headers=error.headers,
    )


async def validation_exception_handler(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    """Return a stable error body for FastAPI/Pydantic validation failures."""
    details = []
    for item in error.errors():
        location = ".".join(str(part) for part in item.get("loc", ()))
        details.append(
            {
                "field": location,
                "message": item.get("msg", "Invalid value."),
                "type": item.get("type"),
            }
        )

    return JSONResponse(
        status_code=UNPROCESSABLE_CONTENT,
        content=_payload(
            "The request data is invalid.",
            VALIDATION_ERROR,
            details,
        ),
    )


async def unhandled_exception_handler(
    request: Request,
    error: Exception,
) -> JSONResponse:
    """Return a generic 500 response without leaking implementation details."""
    logger.exception("Unhandled error while processing %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_payload("An unexpected error occurred.", INTERNAL_ERROR),
    )


def install_error_handlers(app: FastAPI) -> None:
    """Register the handlers that enforce the public error contract."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
