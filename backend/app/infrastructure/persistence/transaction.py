"""PostgreSQL transaction manager built on the async pool of E2-05."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from app.application.ports.transaction_manager import TransactionManager


class PostgresTransactionManager(TransactionManager):
    """One connection and one transaction shared by every repository of a request.

    The manager is created per request (or per test) and handed to the
    repositories as a connection provider, so several repositories can take part
    in the same transaction without the application layer knowing psycopg.
    """

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool
        self._connection: AsyncConnection | None = None

    def transaction(self) -> AbstractAsyncContextManager[None]:
        return self._transaction_scope()

    @asynccontextmanager
    async def _transaction_scope(self) -> AsyncIterator[None]:
        if self._connection is not None:
            # A nested ``transaction()`` joins the outer one instead of
            # opening a second connection and a second transaction.
            yield
            return

        async with self._pool.connection() as connection:
            self._connection = connection
            try:
                async with connection.transaction():
                    yield
            finally:
                self._connection = None

    @property
    def connection(self) -> AsyncConnection:
        """Connection bound to the current transaction."""
        if self._connection is None:
            raise RuntimeError(
                "There is no active transaction. Use "
                "`async with transaction_manager.transaction():` before calling "
                "a repository."
            )
        return self._connection
