"""Test database support for integration tests.

Creates a dedicated PostgreSQL test database (name must end in ``_test``),
applies every schema script from ``backend/database/scripts/`` in order from
Python (no ``psql`` dependency), and wipes all data between tests so each test
starts from a clean slate.

Destructive cleanup is blocked unless the database name ends in ``_test``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import get_settings
from app.infrastructure.persistence.connection import (
    close_db_pool,
    init_db_pool,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = REPO_ROOT / "backend" / "database" / "scripts"

TEST_DB_NAME = "basedebatos_test"
TEST_DB_USER = "basedebatos"
TEST_DB_PASSWORD = "basedebatos"
TEST_DB_HOST = "localhost"
TEST_DB_PORT = 5432

# Scripts must be applied in this numeric order.
SCRIPT_FILES = [
    "001_identity_and_sites.sql",
    "002_catalogs_and_programs.sql.sql",
    "003_exercises_authorisations_enrolments.sql",
    "004_routines_and_structure.sql",
    "005_validation_assignments_sessions_adjustments.sql",
    "006_integrity_constraints.sql",
    "007_consistency_triggers.sql",
    "008_catalog_seeds.sql",
    "010_add_user_is_active.sql",
    "011_routine_parameters_full_generation.sql",
]

_pool: Optional[AsyncConnectionPool] = None


def _test_db_dsn() -> str:
    return (
        f"host={TEST_DB_HOST} port={TEST_DB_PORT} "
        f"dbname=postgres user={TEST_DB_USER} password={TEST_DB_PASSWORD}"
    )


def _target_db_dsn() -> str:
    return (
        f"host={TEST_DB_HOST} port={TEST_DB_PORT} "
        f"dbname={TEST_DB_NAME} user={TEST_DB_USER} password={TEST_DB_PASSWORD}"
    )


def _guard_test_database_name(name: str) -> None:
    """Refuse to operate on a database whose name does not end in ``_test``."""
    if not name.endswith("_test"):
        raise ValueError(
            f"Test database name must end in '_test', got {name!r}. "
            "Destructive cleanup is only allowed on test databases."
        )


async def create_test_database() -> None:
    """Create the dedicated test database if it does not exist yet."""
    _guard_test_database_name(TEST_DB_NAME)
    conn = psycopg.connect(_test_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (TEST_DB_NAME,),
            )
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        conn.close()


async def drop_test_database() -> None:
    """Drop the test database. Only allowed when the name ends in ``_test``."""
    _guard_test_database_name(TEST_DB_NAME)
    # Terminate other connections to the test database before dropping it.
    admin = psycopg.connect(_test_db_dsn(), autocommit=True)
    try:
        with admin.cursor() as cur:
            cur.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid()
                """,
                (TEST_DB_NAME,),
            )
            cur.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
    finally:
        admin.close()


async def apply_schema_scripts() -> None:
    """Apply every schema script in order to the test database."""
    _guard_test_database_name(TEST_DB_NAME)
    conn = psycopg.connect(_target_db_dsn(), autocommit=True)
    try:
        with conn.cursor() as cur:
            for script_name in SCRIPT_FILES:
                script_path = SCRIPTS_DIR / script_name
                if not script_path.exists():
                    raise FileNotFoundError(
                        f"Schema script not found: {script_path}"
                    )
                sql = script_path.read_text(encoding="utf-8")
                cur.execute(sql)
    finally:
        conn.close()


async def init_test_pool() -> AsyncConnectionPool:
    """Initialize and return the application pool pointing at the test DB."""
    global _pool
    if _pool is not None:
        return _pool

    settings = get_settings()
    # Override the database name to point at the test database.
    _pool = AsyncConnectionPool(
        conninfo=_target_db_dsn(),
        min_size=1,
        max_size=5,
        timeout=30,
        open=False,
        kwargs={"row_factory": dict_row},
        name="basedebatos-test-pool",
    )
    await _pool.open(wait=True, timeout=30)
    return _pool


async def close_test_pool() -> None:
    """Close the test pool if it is open."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_test_pool() -> AsyncConnectionPool:
    """Return the open test pool or initialize it."""
    if _pool is None:
        return await init_test_pool()
    return _pool


async def clean_all_tables() -> None:
    """Delete all rows from every application table, respecting FK order.

    Safe to call between tests. Uses TRUNCATE ... CASCADE so ordering does not
    matter.
    """
    _guard_test_database_name(TEST_DB_NAME)
    pool = await get_test_pool()
    async with pool.connection() as conn:
        async with conn.transaction():
            await conn.execute("TRUNCATE TABLE adjustment_result, request, session, assignment, validate, contains, routine_structure, routine, parameters_routine, inscription, authorises, exercise, client, trainer, app_user, muscle_group, exercise_type, intensity_level, workout_program, site, covers RESTART IDENTITY CASCADE")
