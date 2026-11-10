"""Translate application errors into stable HTTP responses."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    ApplicationError,
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)

logger = logging.getLogger(__name__)


def _response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message},
    )


async def application_error_handler(
    request: Request,
    error: ApplicationError,
) -> JSONResponse:
    """Handle known application failures without leaking implementation data."""
    if isinstance(error, ResourceNotFound):
        return _response(404, "resource_not_found", str(error))
    if isinstance(error, DuplicateResource):
        return _response(409, "duplicate_resource", error.detail)
    if isinstance(error, PermissionDenied):
        return _response(403, "permission_denied", error.detail)
    if isinstance(error, InvalidInput):
        return _response(422, "invalid_input", error.detail)
    if isinstance(error, BusinessRuleViolation):
        return _response(409, "business_rule_violation", error.detail)
    return _response(500, "internal_error", "An unexpected error occurred.")


async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
    """Return a generic response and log unexpected failures server-side."""
    logger.exception("Unexpected API error", exc_info=error)
    return _response(500, "internal_error", "An unexpected error occurred.")
