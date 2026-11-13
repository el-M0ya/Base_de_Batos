"""Contract of the transaction manager.

The transaction manager is a per-request context manager: it commits when the
block completes successfully and rolls back on any exception. Repository
adapters obtain their connection from it, so multiple repositories can join the
same transaction without the application layer knowing psycopg.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TransactionManager(ABC):
    """Per-request transaction boundary.

    Use it as an async context manager. While inside the block, call
    :meth:`connection` to get the raw connection and share it with every
    repository that must participate in the same unit of work.
    """

    @abstractmethod
    async def __aenter__(self) -> "TransactionManager":
        """Open the transaction and return this manager."""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Commit on success, roll back on exception, then release the connection."""

    @abstractmethod
    def connection(self) -> Optional[object]:
        """Return the raw connection held by this transaction, or ``None``."""
