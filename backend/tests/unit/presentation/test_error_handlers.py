"""Unit tests for the stable HTTP error contract."""

from __future__ import annotations

import json
import unittest

from fastapi import Request

from app.adapters.presentation.api.error_handlers import (
    application_error_handler,
    unexpected_error_handler,
)
from app.application.exceptions import (
    ApplicationError,
    BusinessRuleViolation,
    DuplicateResource,
    InvalidInput,
    PermissionDenied,
    ResourceNotFound,
)


class ErrorHandlerTests(unittest.IsolatedAsyncioTestCase):
    """Verify application error mappings."""

    request = Request(
        {"type": "http", "method": "GET", "path": "/test", "headers": []}
    )

    @staticmethod
    def body(response: object) -> dict[str, str]:
        content = getattr(response, "body", None)
        if not isinstance(content, bytes):
            raise AssertionError("Expected a JSON response body.")
        value = json.loads(content.decode("utf-8"))
        if not isinstance(value, dict) or not all(
            isinstance(key, str) and isinstance(item, str)
            for key, item in value.items()
        ):
            raise AssertionError("Expected a string error response.")
        return value

    async def assert_mapping(
        self, error: ApplicationError, status_code: int, code: str
    ) -> None:
        response = await application_error_handler(self.request, error)
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(self.body(response)["code"], code)

    async def test_not_found(self) -> None:
        await self.assert_mapping(ResourceNotFound("exercise", 1), 404, "resource_not_found")

    async def test_duplicate(self) -> None:
        await self.assert_mapping(
            DuplicateResource("exercise", "same name"), 409, "duplicate_resource"
        )

    async def test_permission_denied(self) -> None:
        await self.assert_mapping(
            PermissionDenied("trainer required"), 403, "permission_denied"
        )

    async def test_invalid_input(self) -> None:
        await self.assert_mapping(InvalidInput("invalid name"), 422, "invalid_input")

    async def test_business_rule(self) -> None:
        await self.assert_mapping(
            BusinessRuleViolation("not allowed"), 409, "business_rule_violation"
        )

    async def test_unexpected_error_is_generic(self) -> None:
        response = await unexpected_error_handler(
            self.request, RuntimeError("internal database detail")
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            self.body(response),
            {"code": "internal_error", "message": "An unexpected error occurred."},
        )
