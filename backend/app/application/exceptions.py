"""Errors raised by the application layer.

Each error represents one of the five situations the layer has to report to its
callers, independently of the delivery mechanism (HTTP, CLI, tests...):

* ``ResourceNotFound``        - the referenced resource does not exist;
* ``DuplicateResource``       - the resource violates a uniqueness rule;
* ``BusinessRuleViolation``   - the operation is valid but not allowed now;
* ``PermissionDenied``        - the actor cannot perform the operation;
* ``InvalidInput``            - the supplied data is not valid;
* ``AuthenticationFailed``    - the credentials do not identify an active account;
* ``InvalidToken``            - the access token is invalid or unusable;
* ``ExpiredToken``            - the access token has expired.

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


class AuthenticationFailed(ApplicationError):
    """The supplied credentials are missing, invalid, or belong to an inactive account."""

    def __init__(self, detail: str = "Invalid email or password.") -> None:
        self.detail = detail
        super().__init__(detail)


class InvalidToken(ApplicationError):
    """The access token is malformed, has an invalid signature, or is not usable."""

    def __init__(self, detail: str = "The access token is invalid.") -> None:
        self.detail = detail
        super().__init__(detail)


class ExpiredToken(InvalidToken):
    """The access token was valid but its expiration time has passed."""

    def __init__(self, detail: str = "The access token has expired.") -> None:
        super().__init__(detail)
