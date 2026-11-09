"""Errors raised by the application layer.

Each error represents one of the five situations the layer has to report to its
callers, independently of the delivery mechanism (HTTP, CLI, tests...):

* ``ResourceNotFound``        - the referenced resource does not exist;
* ``DuplicateResource``       - the resource violates a uniqueness rule;
* ``BusinessRuleViolation``   - the operation is valid but not allowed now;
* ``PermissionDenied``        - the actor cannot perform the operation;
* ``InvalidInput``            - the supplied data is not valid.

Domain errors are translated to ``InvalidInput`` at the use-case boundary, so
callers never depend on the domain exception hierarchy.
"""

from __future__ import annotations

from typing import Optional


class ApplicationError(Exception):
    """Base class of every application error."""


class ResourceNotFound(ApplicationError):
    """The caller referenced a resource that does not exist."""

    def __init__(self, resource: str, identifier: object) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"The {resource} {identifier!r} does not exist.")


class DuplicateResource(ApplicationError):
    """The operation would create a duplicated resource."""

    def __init__(
        self,
        resource: str,
        detail: str,
        *,
        existing: Optional[object] = None,
    ) -> None:
        self.resource = resource
        self.detail = detail
        self.existing = existing
        super().__init__(f"Duplicated {resource}: {detail}")


class BusinessRuleViolation(ApplicationError):
    """The operation breaks a business rule in the current state."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Business rule violation: {detail}")


class PermissionDenied(ApplicationError):
    """The actor is authenticated but is not allowed to perform the operation."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Permission denied: {detail}")


class InvalidInput(ApplicationError):
    """The supplied data does not satisfy the domain rules."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Invalid input: {detail}")
