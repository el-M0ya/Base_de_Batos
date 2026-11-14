"""psycopg implementation of :class:`app.application.ports.transaction_manager.TransactionManager`.

Obtains a connection from the process-wide pool and keeps it for the lifetime of
the ``async with`` block: commits on clean exit, rolls back on any exception,
and returns the connection to the pool on exit.
"""

from __future__ import annotations

from contextlib import AsyncExitStack
from typing import Optional

from psycopg import AsyncConnection

from app.application.ports.transaction_manager import TransactionManager
from app.infrastructure.persistence.connection import connection_scope


class PsqlTransactionManager(TransactionManager):
    """Transactional boundary backed by the psycopg async pool."""

    def __init__(self) -> None:
        self._connection: Optional[AsyncConnection] = None
        self._stack: Optional[AsyncExitStack] = None

    async def __aenter__(self) -> "PsqlTransactionManager":
        self._stack = AsyncExitStack()
        self._connection = await self._stack.enter_async_context(connection_scope())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._stack is None:
            return
        stack = self._stack
        self._stack = None
        self._connection = None
        await stack.__aexit__(exc_type, exc_val, exc_tb)

    def connection(self) -> Optional[AsyncConnection]:
        """Return the connection held by this transaction, or ``None`` outside it."""
        return self._connection
