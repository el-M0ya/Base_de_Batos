"""Integration tests for the direct psycopg connection to PostgreSQL.

These tests require a running PostgreSQL instance. They are skipped (not
failed) when the database is unavailable, so the unit-test workflow can run
on machines without Docker."""

from __future__ import annotations

import asyncio

import psycopg
import pytest

from app.core.config import get_settings
from app.infrastructure.persistence.connection import (
    close_db_pool,
    connection_scope,
    init_db_pool,
    transaction_scope,
)

pytestmark = pytest.mark.integration


def _postgres_is_available() -> bool:
    try:
        with psycopg.connect(get_settings().database_url, connect_timeout=3):
            return True
    except (psycopg.Error, OSError):
        return False


@pytest.fixture(scope="module", autouse=True)
def require_postgres() -> None:
    if not _postgres_is_available():
        pytest.skip(
            "PostgreSQL is not available. Start it with "
            "`docker compose up -d --wait` and check POSTGRES_* in the "
            "environment or .env file."
        )


def test_pool_executes_a_parameterized_query() -> None:
    async def scenario() -> None:
        await init_db_pool()
        try:
            async with connection_scope() as connection:
                cursor = await connection.execute(
                    "SELECT %s::integer AS value",
                    (42,),
                )
                row = await cursor.fetchone()
                assert row == {"value": 42}
        finally:
            await close_db_pool()

    asyncio.run(scenario())


def test_transaction_scope_rolls_back_and_pool_stays_usable() -> None:
    async def scenario() -> None:
        await init_db_pool()
        try:
            with pytest.raises(RuntimeError, match="forced rollback"):
                async with transaction_scope() as connection:
                    await connection.execute("SELECT 1")
                    raise RuntimeError("forced rollback")

            async with connection_scope() as connection:
                cursor = await connection.execute("SELECT 2::integer AS value")
                row = await cursor.fetchone()
                assert row == {"value": 2}
        finally:
            await close_db_pool()

    asyncio.run(scenario())


def test_connection_uses_the_configured_database_and_user() -> None:
    async def scenario() -> None:
        settings = get_settings()
        await init_db_pool()
        try:
            async with connection_scope() as connection:
                cursor = await connection.execute(
                    "SELECT current_database() AS database_name, "
                    "current_user AS user_name"
                )
                row = await cursor.fetchone()
                assert row is not None
                assert row["database_name"] == settings.postgres_db
                assert row["user_name"] == settings.postgres_user
        finally:
            await close_db_pool()

    asyncio.run(scenario())