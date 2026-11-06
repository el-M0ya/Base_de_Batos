"""Async PostgreSQL connection pool and lifecycle helpers.

The rest of the application must obtain connections through this module:
it centralizes the pool, transaction boundaries and row mapping. No ORM is
used; queries stay explicit and parameterized."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import get_settings

_pool: AsyncConnectionPool | None = None


async def init_db_pool() -> AsyncConnectionPool:
    """Create and open the process-wide pool. Safe to call more than once."""
    global _pool

    if _pool is not None:
        return _pool

    settings = get_settings()
    pool = AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        timeout=settings.db_pool_timeout_seconds,
        open=False,
        kwargs={"row_factory": dict_row},
        name="basedebatos-pool",
    )

    try:
        await pool.open(wait=True, timeout=settings.db_pool_timeout_seconds)
    except BaseException:
        await pool.close()
        raise

    _pool = pool
    return _pool


async def close_db_pool() -> None:
    """Close the pool and release every PostgreSQL connection."""
    global _pool

    if _pool is None:
        return

    pool = _pool
    _pool = None
    await pool.close()


def get_db_pool() -> AsyncConnectionPool:
    """Return the open pool or fail with a clear message."""
    if _pool is None:
        raise RuntimeError(
            "The PostgreSQL pool is not initialized. "
            "Call init_db_pool() during application startup."
        )
    return _pool


@asynccontextmanager
async def connection_scope() -> AsyncIterator[AsyncConnection]:
    """Borrow a connection and return it to the pool when the block ends.

    The pool commits the transaction if the block exits normally and rolls
    it back if an exception is raised."""
    pool = get_db_pool()
    async with pool.connection() as connection:
        yield connection


@asynccontextmanager
async def transaction_scope() -> AsyncIterator[AsyncConnection]:
    """Run a block inside an explicit transaction."""
    async with connection_scope() as connection:
        async with connection.transaction():
            yield connection


async def get_db_connection() -> AsyncIterator[AsyncConnection]:
    """FastAPI dependency that yields a pooled connection.

    Use it with ``Depends(get_db_connection)`` once routers are implemented."""
    async with connection_scope() as connection:
        yield connection