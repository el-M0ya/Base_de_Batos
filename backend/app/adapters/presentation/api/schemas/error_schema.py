"""Stable error response schema."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Public error contract; internal exception details are not exposed."""

    code: str
    message: str
