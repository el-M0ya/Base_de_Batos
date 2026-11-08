"""Transaction boundary contract of the application layer.

The application layer opens a transactional unit of work and expects every
repository used inside it to share the same database transaction. It never sees
a psycopg connection: the infrastructure adapter owns that detail.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager


class TransactionManager(ABC):
    """Commit on success and roll back when the block raises."""

    @abstractmethod
    def transaction(self) -> AbstractAsyncContextManager[None]:
        """Enter a transaction scope shared by the repositories of the request."""
