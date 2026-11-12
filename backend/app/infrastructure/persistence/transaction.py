"""psycopg implementation of :class:`app.application.ports.transaction_manager.TransactionManager`.

Obtains a connection from the process-wide pool and keeps it for the lifetime of
the ``async with`` block: commits on clean exit, rolls back on any exception,
and returns the connection to the pool on exit.
"""

from __future__ import annotations

from typing import Optional

from psycopg import AsyncConnection

from app.application.ports.transaction_manager import TransactionManager
from app.infrastructure.persistence.connection import get_db_pool


class PsqlTransactionManager(TransactionManager):
    """Transactional boundary backed by the psycopg async pool."""

    def __init__(self) -> None:
        self._connection: Optional[AsyncConnection] = None

    async def __aenter__(self) -> "PsqlTransactionManager":
        pool = get_db_pool()
        self._connection = await pool.connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._connection is None:
            return
        try:
            if exc_type is None:
                await self._connection.commit()
            else:
                await self._connection.rollback()
        finally:
            await self._connection.close()
            self._connection = None

    def connection(self) -> Optional[AsyncConnection]:
        """Return the connection held by this transaction, or ``None`` outside it."""
        return self._connection
