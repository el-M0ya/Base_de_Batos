"""Domain layer exceptions."""

from __future__ import annotations


class DomainException(Exception):
    """Base of all domain exceptions."""


# ---------------------------------------------------------------------------
# Values and general invariants
# ---------------------------------------------------------------------------
class InvalidDomainValue(DomainException):
    """Invalid domain values"""

    def __init__(self, field: str, value: object, expected: str) -> None:
        self.field = field
        self.value = value
        self.expected = expected
        super().__init__(
            f"Invalid value for '{field}': {value!r}. Was expected {expected}."
        )


class InvalidDateRange(DomainException):
    """Inconsistent date range (end before start)."""

    def __init__(self, start_field: str, end_field: str, start: object, end: object) -> None:
        self.start_field = start_field
        self.end_field = end_field
        super().__init__(
            f"'{end_field}' ({end!r}) can't be before "
            f"'{start_field}' ({start!r})."
        )


# ---------------------------------------------------------------------------
# Routine
# ---------------------------------------------------------------------------
class InvalidRoutineStateTransition(DomainException):
    """An unauthorized state transition was attempted in a routine."""

    def __init__(self, current: object, target: object) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Can't skip the routine of '{current}' to '{target}'."
        )


class InvalidRoutineReference(DomainException):
    """Invalid reference between routines (for example, source = itself)."""

    def __init__(self, routine_id: object, origin_id: object) -> None:
        self.routine_id = routine_id
        self.origin_id = origin_id
        super().__init__(
            f"The routine {routine_id!r} cannot have as its origin {origin_id!r}."
        )


# ---------------------------------------------------------------------------
# Routine generation strategy
# ---------------------------------------------------------------------------
class UnknownGenerationStrategy(DomainException):
    """A routine-generation strategy name is not present in the registry."""

    def __init__(self, name: object, available: tuple[str, ...] = ()) -> None:
        self.name = name
        self.available = available
        available_names = ", ".join(available) if available else "none"
        super().__init__(
            f"Unknown routine generation strategy {name!r}. "
            f"Available strategies: {available_names}."
        )


# ---------------------------------------------------------------------------
# enGeration parameters
# ---------------------------------------------------------------------------
class InvalidParameters(DomainException):
    """The generation parameters don't meet their constraints."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Invalid routine parameters: {detail}")


# ---------------------------------------------------------------------------
# Variable structure (JSONB)
# ---------------------------------------------------------------------------
class InvalidStructure(DomainException):
    """The block hierarchy of the routine is not valid."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Invalid routine structure: {detail}")


class StructureNotJsonSerializable(DomainException):
    """The structure contains values that can't be converted to JSON."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(
            f"The routine structure can't be serialized to JSON: {detail}"
        )


# ---------------------------------------------------------------------------
# Validation (review by the floor manager)
# ---------------------------------------------------------------------------
class ValidationNotAllowed(DomainException):
    """The routine can't be validated in its current state."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Validation not allowed: {detail}")


class RejectedValidationRequiresObservations(DomainException):
    """A REJECTED decision requires non-empty remarks."""

    def __init__(self) -> None:
        super().__init__(
            "A validation with a 'REJECTED' decision requires comments."
        )


class InvalidValidationDate(DomainException):
    """The validation date is before the creation of the routine."""

    def __init__(self, validation_date: object, creation_date: object) -> None:
        self.validation_date = validation_date
        self.creation_date = creation_date
        super().__init__(
            f"The validation date ({validation_date!r}) it can't be earlier" 
            f"than the creation date of the routine ({creation_date!r})."
        )


# ---------------------------------------------------------------------------
# Asiggnation
# ---------------------------------------------------------------------------
class AssignmentNotAllowed(DomainException):
    """Assigning a routine to a client doesn't follow the rules."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Asiggnation not allowed: {detail}")


# ---------------------------------------------------------------------------
# Training session
# ---------------------------------------------------------------------------
class InvalidSessionData(DomainException):
    """The data from a training session doesn't make sense."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Invalid training session: {detail}")


class SessionNotAllowed(DomainException):
    """The session does not correspond to a valid assignment."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Session not allowed: {detail}")


# ---------------------------------------------------------------------------
# Adjustment request
# ---------------------------------------------------------------------------
class InvalidRequestStateTransition(DomainException):
    """State transition not allowed in a adjustment request."""

    def __init__(self, current: object, target: object) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"The adjustment request can't be processed for '{current}' to '{target}'."
        )


class RequestNotAllowed(DomainException):
    """The adjustment request does not meet the business rules."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Adjustment request not allowed: {detail}")


class PendingRequestAlreadyExists(DomainException):
    """There’s already a pending request for the same routine and client."""

    def __init__(self, id_routine: object) -> None:
        self.id_routine = id_routine
        super().__init__(
            f"There is already a pending adjustment request for the routine"
            f"{id_routine!r}."
        )


# ---------------------------------------------------------------------------
# Adjustment result
# ---------------------------------------------------------------------------
class AdjustmentTrainerMismatch(DomainException):
    """The coach who handles it isn't the one assigned in the request."""

    def __init__(self, expected: object, received: object) -> None:
        self.expected = expected
        self.received = received
        super().__init__(
            f" The resolving coach ({received!r}) does not match the "
            f"coach assigned in the request ({expected!r})."
        )


class ResultBeforeRequest(DomainException):
    """The result was recorded before the request."""

    def __init__(self, response_date: object, request_date: object) -> None:
        self.response_date = response_date
        self.request_date = request_date
        super().__init__(
            f"The response date ({response_date!r}) can't be before "
            f"the request date ({request_date!r})."
        )


class AdjustmentResultNotAllowed(DomainException):
    """The adjustment result does not meet the business rules."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Adjustment result not allowed: {detail}")
